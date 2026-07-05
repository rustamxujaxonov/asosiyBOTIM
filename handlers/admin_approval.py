"""
handlers/admin_approval.py
-------------------------------
Admin guruhidagi "✅ Tasdiqlash" / "❌ Rad etish" tugmalari.

Tasdiqlanganda:
    - Foydalanuvchining premium_until sanasi paket kuniga qarab uzaytiriladi.
    - Foydalanuvchiga tasdiqlash xabari va tugash sanasi yuboriladi.
    - Admin guruhidagi xabar tahrirlanadi (qayta bosilmasligi uchun tugmalar olib tashlanadi).

Rad etilganda:
    - Foydalanuvchiga rad etilgani haqida xabar boradi.
    - Admin guruhidagi xabar tahrirlanadi.
"""

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PACKAGE_DAYS, PACKAGE_LABELS, PaymentStatusEnum
from database.requests import extend_premium, get_payment_request, resolve_payment_request
from keyboards.inline import AdminApprovePayment, AdminRejectPayment

router = Router(name="admin_approval")


@router.callback_query(AdminApprovePayment.filter())
async def approve_payment(
    callback: CallbackQuery, callback_data: AdminApprovePayment, session: AsyncSession, bot: Bot
) -> None:
    """To'lovni tasdiqlaydi, Premium muddatini uzaytiradi va foydalanuvchiga xabar beradi."""
    payment = await get_payment_request(session, callback_data.payment_id)

    if payment is None:
        await callback.answer("⚠️ To'lov topilmadi (ehtimol, allaqachon ishlov berilgan).", show_alert=True)
        return

    if payment.status != PaymentStatusEnum.PENDING:
        await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    days = PACKAGE_DAYS[payment.package]
    premium_until = await extend_premium(session, payment.user_id, days)

    await resolve_payment_request(session, payment.id, PaymentStatusEnum.APPROVED)

    await callback.answer("✅ Tasdiqlandi!")

    # Admin guruhidagi xabarni yangilaymiz (tugmalarsiz, holat bilan)
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>TASDIQLANDI</b>",
        reply_markup=None,
    )

    try:
        await bot.send_message(
            chat_id=payment.user_id,
            text=(
                "🎉 Obunangiz tasdiqlandi!\n\n"
                f"📦 Paket: {PACKAGE_LABELS[payment.package]}\n"
                f"⏰ Tugash vaqti: {premium_until.strftime('%Y-%m-%d %H:%M')}\n\n"
                "Endi Premium xususiyatlardan to'liq foydalanishingiz mumkin!"
            ),
        )
    except Exception:
        # Foydalanuvchi botni bloklagan bo'lishi mumkin — admin xabari baribir yangilandi
        pass


@router.callback_query(AdminRejectPayment.filter())
async def reject_payment(
    callback: CallbackQuery, callback_data: AdminRejectPayment, session: AsyncSession, bot: Bot
) -> None:
    """To'lovni rad etadi va foydalanuvchiga xabar beradi."""
    payment = await get_payment_request(session, callback_data.payment_id)

    if payment is None:
        await callback.answer("⚠️ To'lov topilmadi.", show_alert=True)
        return

    if payment.status != PaymentStatusEnum.PENDING:
        await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await resolve_payment_request(session, payment.id, PaymentStatusEnum.REJECTED)

    await callback.answer("❌ Rad etildi.")

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>",
        reply_markup=None,
    )

    try:
        await bot.send_message(
            chat_id=payment.user_id,
            text=(
                "❌ Afsuski, sizning to'lov chekingiz rad etildi.\n\n"
                "Iltimos, to'lov ma'lumotlarini tekshirib, qaytadan urinib ko'ring "
                "yoki admin bilan bog'laning."
            ),
        )
    except Exception:
        pass
