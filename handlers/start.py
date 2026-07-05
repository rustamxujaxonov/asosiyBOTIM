"""
handlers/start.py
--------------------
/start komandasi.

Vazifalari:
    1. Foydalanuvchini bazadan topish yoki yaratish (referal ID bilan birga).
    2. Agar ro'yxatdan o'tmagan bo'lsa -> ro'yxatdan o'tish jarayonini boshlash.
    3. Agar ro'yxatdan o'tgan bo'lsa -> asosiy menyuni ko'rsatish.

ESLATMA: Majburiy obuna tekshiruvi SubscriptionMiddleware orqali avtomatik
amalga oshiriladi — bu handler ishga tushgan payt foydalanuvchi allaqachon obuna bo'lgan.
"""

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import get_or_create_user
from keyboards.reply import main_menu_keyboard
from states.states import RegistrationStates

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, state: FSMContext, session: AsyncSession
) -> None:
    """/start komandasini qayta ishlaydi, referal parametrini o'qiydi."""
    await state.clear()

    # Referal ID'ni o'qish: /start 123456789 -> referrer_id = 123456789
    referrer_id: int | None = None
    if command.args and command.args.isdigit():
        referrer_id = int(command.args)

    user, is_new = await get_or_create_user(
        session=session,
        user_id=message.from_user.id,
        username=message.from_user.username,
        referrer_id=referrer_id,
    )

    if not user.is_registered:
        await message.answer(
            "👋 Assalomu alaykum! Botimizga xush kelibsiz.\n\n"
            "Anonim tanishuvlar dunyosiga qadam qo'yish uchun avval "
            "qisqacha ro'yxatdan o'tishimiz kerak.\n\n"
            "✍️ Ismingizni kiriting:"
        )
        await state.set_state(RegistrationStates.waiting_full_name)
        return

    await message.answer(
        f"Xush kelibsiz, {user.full_name}! 😊\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(),
    )
