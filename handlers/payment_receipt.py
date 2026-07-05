"""
handlers/payment_receipt.py
--------------------------------
Foydalanuvchi Premium paket tanlagandan so'ng yuborgan chek rasmini qabul qiladi,
bazaga PaymentRequest sifatida yozadi va admin guruhiga (ADMIN_GROUP_ID) yuboradi.
"""

from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.models import PACKAGE_LABELS, PACKAGE_PRICES
from database.requests import create_payment_request, set_admin_message_id
from keyboards.inline import admin_payment_keyboard
from keyboards.reply import main_menu_keyboard
from states.states import PaymentStates

router = Router(name="payment_receipt")


@router.message(PaymentStates.waiting_receipt_photo, lambda m: m.photo is not None)
async def process_receipt_photo(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot, config: Config
) -> None:
    """Chek rasmi qabul qilinganda: bazaga yozadi, admin guruhiga yuboradi."""
    data = await state.get_data()
    package = data.get("selected_package")

    if package is None:
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qaytadan paket tanlang.")
        await state.clear()
        return

    price = PACKAGE_PRICES[package]
    label = PACKAGE_LABELS[package]

    # Eng katta o'lchamdagi rasm variantini olamiz (Telegram bir nechta o'lchamda yuboradi)
    photo_file_id = message.photo[-1].file_id

    payment = await create_payment_request(
        session=session,
        user_id=message.from_user.id,
        package=package,
        amount=price,
        photo_file_id=photo_file_id,
    )

    await state.clear()

    await message.answer(
        "✅ Sizning chekingiz adminlarga yuborildi.\n"
        "⏳ Tasdiqlash 10-15 daqiqa vaqt olishi mumkin. Iltimos, kuting.",
        reply_markup=main_menu_keyboard(),
    )

    username_display = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

    admin_caption = (
        "🧾 <b>Yangi to'lov cheki</b>\n\n"
        f"👤 Foydalanuvchi ID: <code>{message.from_user.id}</code>\n"
        f"📛 Username: {username_display}\n"
        f"📦 Paket: {label}\n"
        f"💰 Summasi: {price:,} so'm\n".replace(",", " ") +
        f"🆔 To'lov ID: {payment.id}"
    )

    try:
        admin_message = await bot.send_photo(
            chat_id=config.bot.admin_group_id,
            photo=photo_file_id,
            caption=admin_caption,
            reply_markup=admin_payment_keyboard(payment.id),
        )
        await set_admin_message_id(session, payment.id, admin_message.message_id)
    except Exception:
        # Admin guruhi ID noto'g'ri yoki bot guruhda yo'q bo'lishi mumkin
        await message.answer(
            "⚠️ Chekni adminlarga yuborishda texnik xatolik yuz berdi. "
            "Iltimos, admin bilan to'g'ridan-to'g'ri bog'laning."
        )


@router.message(PaymentStates.waiting_receipt_photo)
async def invalid_receipt(message: Message) -> None:
    """Agar foydalanuvchi rasm o'rniga boshqa turdagi xabar yuborsa."""
    await message.answer("⚠️ Iltimos, to'lov chekining rasmini (screenshot/photo) yuboring.")
