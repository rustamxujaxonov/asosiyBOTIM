"""
handlers/profile.py
-----------------------
"Mening profilim 👤" bo'limi.

Foydalanuvchining Ism, Yosh, Jins, Viloyat, Premium statusi va
taklif qilgan do'stlar sonini ko'rsatadi.
"""

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import get_user
from keyboards.reply import BTN_MY_PROFILE

router = Router(name="profile")


@router.message(lambda m: m.text == BTN_MY_PROFILE)
async def show_profile(message: Message, session: AsyncSession) -> None:
    """Foydalanuvchi profilini chiroyli formatda ko'rsatadi."""
    user = await get_user(session, message.from_user.id)

    if user is None or not user.is_registered:
        await message.answer("⚠️ Profilingiz topilmadi. Iltimos, /start buyrug'ini qayta yuboring.")
        return

    if user.is_premium():
        premium_status = f"✅ Aktiv ({user.premium_until.strftime('%Y-%m-%d %H:%M')} gacha)"
    else:
        premium_status = "❌ Aktiv emas"

    gender_display = "Yigit 🚹" if user.gender and user.gender.value == "yigit" else "Qiz 🚺"

    text = (
        "👤 <b>Mening profilim</b>\n\n"
        f"📝 Ism: {user.full_name}\n"
        f"🎂 Yosh: {user.age}\n"
        f"⚧ Jins: {gender_display}\n"
        f"📍 Viloyat: {user.region}\n"
        f"💎 Premium: {premium_status}\n"
        f"🎁 Taklif qilingan do'stlar: {user.invited_count} ta\n"
    )

    await message.answer(text)
