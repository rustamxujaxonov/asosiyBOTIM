from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, Update

from keyboards.inline import CheckSubscription, subscription_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    """Foydalanuvchi majburiy kanalga obuna bo'lganligini tekshiradi."""

    def __init__(self, channel_id: str, channel_url: str):
        self.channel_id = channel_id
        self.channel_url = channel_url
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,  # Outer middleware uchun bu Update bo'lishi shart
        data: dict[str, Any],
    ) -> Any:
        # Update ichidan haqiqiy eventni (Message yoki CallbackQuery) ajratib olamiz
        actual_event = event.message or event.callback_query

        # Agar bu boshqa turdagi update bo'lsa (masalan, inline_query), o'tkazib yuboramiz
        if not actual_event:
            return await handler(event, data)

        # "Obunani tekshirish" tugmasi bosilganda bloklamaslik
        if event.callback_query and event.callback_query.data == CheckSubscription().pack():
            return await handler(event, data)

        bot: Bot = data["bot"]
        user_id = actual_event.from_user.id

        is_subscribed = await self._check_subscription(bot, user_id)

        if is_subscribed:
            return await handler(event, data)

        # Obuna bo'lmagan foydalanuvchiga xabar ko'rsatamiz
        text = (
            "❗️ Botdan foydalanish uchun avval quyidagi kanalga obuna bo'ling, "
            "so'ngra \"✅ Obunani tekshirish\" tugmasini bosing."
        )
        keyboard = subscription_keyboard(self.channel_url)

        if event.message:
            await event.message.answer(text, reply_markup=keyboard)
        elif event.callback_query:
            await event.callback_query.answer("Avval kanalga obuna bo'ling!", show_alert=True)
            await event.callback_query.message.answer(text, reply_markup=keyboard)

        return None  # Handler zanjirini shu yerda to'xtatamiz

    async def _check_subscription(self, bot: Bot, user_id: int) -> bool:
        """Telegram Bot API orqali foydalanuvchining kanaldagi statusini tekshiradi."""
        try:
            member = await bot.get_chat_member(chat_id=self.channel_id, user_id=user_id)
        except TelegramBadRequest:
            # Bot kanalda admin emas yoki kanal ID noto'g'ri
            return False

        return member.status not in ("left", "kicked")
