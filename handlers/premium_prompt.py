"""
handlers/premium_prompt.py
------------------------------
Premium paketlarni ko'rsatish va referal havolasini berish.

show_premium_offer(...) funksiyasi handlers/search.py'dan chaqiriladi
(foydalanuvchi Premium bo'lmagan holda jinsli qidiruvni tanlaganda).
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.models import PACKAGE_LABELS, PACKAGE_PRICES
from database.requests import get_user
from keyboards.inline import (
    BuyPackageCallback,
    ReferralInfoCallback,
    premium_packages_keyboard,
)
from states.states import PaymentStates

router = Router(name="premium_prompt")


async def show_premium_offer(message: Message, target_gender: str) -> None:
    """
    Premium paketlar ro'yxatini narxlari bilan ko'rsatadi.
    target_gender: keyingi qidiruv qaysi jins bo'yicha bo'lishini "eslab qolish" uchun
    (to'lov tasdiqlangandan keyin darhol shu qidiruvni boshlash mumkin bo'ladi).
    """
    gender_label = "Qiz bolalarni" if target_gender == "qiz" else "Yigitlarni"

    text = (
        f"💎 {gender_label} tanlab qidirish — Premium xususiyat!\n\n"
        "Quyidagi paketlardan birini tanlang:\n\n"
    )

    for package_key, label in PACKAGE_LABELS.items():
        price = PACKAGE_PRICES[package_key]
        text += f"• {label} — {price:,} so'm\n".replace(",", " ")

    text += (
        "\n💳 To'lovni amalga oshirgach, chek rasmini botga yuboring.\n"
        "Admin tomonidan tasdiqlangach, Premium avtomatik faollashadi."
    )

    await message.answer(text, reply_markup=premium_packages_keyboard(target_gender))


@router.callback_query(BuyPackageCallback.filter())
async def choose_package(
    callback: CallbackQuery, callback_data: BuyPackageCallback, state: FSMContext, config: Config
) -> None:
    """
    Foydalanuvchi paketni tanlaganda, to'lov ma'lumotlarini (karta raqami, egasi)
    ko'rsatadi va chek rasmini kutish holatiga o'tkazadi.
    """
    package = callback_data.package
    label = PACKAGE_LABELS[package]
    price = PACKAGE_PRICES[package]

    await state.update_data(selected_package=package, target_gender=callback_data.target_gender)
    await state.set_state(PaymentStates.waiting_receipt_photo)

    text = (
        f"Siz \"{label}\" paketini tanladingiz — {price:,} so'm.\n\n".replace(",", " ")
        + "💳 To'lovni quyidagi kartaga amalga oshiring:\n\n"
        f"💳 Karta raqami: <code>{config.payment.card_number}</code>\n"
        f"👤 Karta egasi: {config.payment.card_owner}\n\n"
        "✅ To'lovni amalga oshirgach, chek (screenshot) rasmini shu yerga yuboring."
    )

    await callback.answer()
    await callback.message.answer(text)


@router.callback_query(ReferralInfoCallback.filter())
async def show_referral_link(callback: CallbackQuery, config: Config, session: AsyncSession) -> None:
    """Foydalanuvchining shaxsiy referal havolasini va joriy holatini ko'rsatadi."""
    user = await get_user(session, callback.from_user.id)
    referral_link = f"https://t.me/{config.bot.bot_username}?start={callback.from_user.id}"

    invited = user.invited_count if user else 0
    remaining = max(0, 5 - invited)

    text = (
        "🎁 <b>Referal orqali bepul Premium</b>\n\n"
        f"Sizning shaxsiy havolangiz:\n{referral_link}\n\n"
        f"👥 Hozircha taklif qilganlar: {invited} ta\n"
        f"⏳ Yana {remaining} ta do'stingiz ro'yxatdan o'tsa — 2 kunlik Premium avtomatik beriladi!\n\n"
        "Havolani do'stlaringizga yuboring va ular botni ishga tushirib, "
        "ro'yxatdan to'liq o'tishlari kifoya."
    )

    await callback.answer()
    await callback.message.answer(text)
