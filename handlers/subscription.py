"""
handlers/subscription.py
---------------------------
"✅ Obunani tekshirish" tugmasi bosilganda ishga tushadigan handler.

Bu handler SubscriptionMiddleware ichida ataylab istisno qilingan,
shuning uchun obuna bo'lmagan foydalanuvchi ham shu tugmani bosa oladi.
Handler o'zi qayta tekshiradi va natijaga qarab javob beradi.
"""

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.requests import get_or_create_user
from keyboards.inline import CheckSubscription
from keyboards.reply import main_menu_keyboard
from states.states import RegistrationStates

router = Router(name="subscription")


@router.callback_query(CheckSubscription.filter())
async def check_subscription_callback(
    callback: CallbackQuery, bot: Bot, config: Config, state: FSMContext, session: AsyncSession
) -> None:
    """Obunani qayta tekshiradi va natijaga qarab ro'yxatdan o'tish yoki menyuni ko'rsatadi."""
    try:
        member = await bot.get_chat_member(
            chat_id=config.bot.channel_id, user_id=callback.from_user.id
        )
        is_subscribed = member.status not in ("left", "kicked")
    except TelegramBadRequest:
        is_subscribed = False

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali kanalga obuna bo'lmadingiz. Iltimos, avval obuna bo'ling.",
            show_alert=True,
        )
        return

    await callback.answer("✅ Obuna tasdiqlandi!")
    await callback.message.delete()

    user, _ = await get_or_create_user(
        session=session,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
    )

    if not user.is_registered:
        await callback.message.answer(
            "Ajoyib! Endi ro'yxatdan o'tamiz.\n\n✍️ Ismingizni kiriting:"
        )
        await state.set_state(RegistrationStates.waiting_full_name)
    else:
        await callback.message.answer(
            "Xush kelibsiz! Quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=main_menu_keyboard(),
        )
