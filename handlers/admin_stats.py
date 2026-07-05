"""
handlers/admin_stats.py
----------------------------
Faqat adminlar uchun oddiy statistika komandasi: /stats

Bu handlerga faqat IsAdmin filtri o'tgan foydalanuvchilar kira oladi
(filters/admin.py'dagi IsAdmin klassiga qarang).
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.models import User
from filters.admin import IsAdmin

router = Router(name="admin_stats")


def register_admin_filter(config: Config) -> None:
    """
    Router'ga IsAdmin filtrini bog'laydi.
    dispatcher.py ichida chaqiriladi (config ma'lum bo'lgandan keyin).
    """
    router.message.filter(IsAdmin(config.bot.admin_ids))


@router.message(Command("stats"))
async def show_stats(message: Message, session: AsyncSession) -> None:
    """Umumiy foydalanuvchilar soni va Premium foydalanuvchilar sonini ko'rsatadi."""
    total_users_result = await session.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar_one()

    registered_result = await session.execute(
        select(func.count(User.id)).where(User.is_registered == True)  # noqa: E712
    )
    registered_users = registered_result.scalar_one()

    from datetime import datetime

    premium_result = await session.execute(
        select(func.count(User.id)).where(User.premium_until > datetime.utcnow())
    )
    premium_users = premium_result.scalar_one()

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"✅ Ro'yxatdan o'tganlar: {registered_users}\n"
        f"💎 Premium foydalanuvchilar: {premium_users}\n"
    )

    await message.answer(text)
