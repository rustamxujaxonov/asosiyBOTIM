"""
middlewares/subscription.py
------------------------------
Majburiy obuna middleware.

Har bir Message va CallbackQuery uchun foydalanuvchining belgilangan kanalga
obuna bo'lganligini tekshiradi. Agar obuna bo'lmasa, botning boshqa hech qanday
handleriga o'tkazmasdan, obuna so'rovini ko'rsatadi.

MUHIM: 'Obunani tekshirish' tugmasi (CheckSubscription callback) o'zi ham
shu middleware orqali o'tadi, shuning uchun uni istisno qilib qo'yamiz —
aks holda foydalanuvchi tugmani bosolmay qoladi (chexicken-and-egg muammosi).
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from keyboards.inline import CheckSubscription, subscription_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    """Foydalanuvchi majburiy kanalga obuna bo'lganligini tekshiradi."""

    def __init__(self, channel_id: str, channel_url: str):
        self.channel_id = channel_id
        self.channel_url = channel_url
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Faqat Message va CallbackQuery uchun tekshiramiz
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        # "Obunani tekshirish" tugmasi bosilganda — bu tekshiruvni handler ichida
        # alohida amalga oshiramiz (foydalanuvchiga tushunarli javob berish uchun),
        # shuning uchun middleware darajasida bloklamaymiz.
        if isinstance(event, CallbackQuery) and event.data == CheckSubscription().pack():
            return await handler(event, data)

        bot: Bot = data["bot"]
        user_id = event.from_user.id

        is_subscribed = await self._check_subscription(bot, user_id)

        if is_subscribed:
            return await handler(event, data)

        # Obuna bo'lmagan foydalanuvchiga xabar ko'rsatamiz
        text = (
            "❗️ Botdan foydalanish uchun avval quyidagi kanalga obuna bo'ling, "
            "so'ngra \"✅ Obunani tekshirish\" tugmasini bosing."
        )
        keyboard = subscription_keyboard(self.channel_url)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:  # CallbackQuery
            await event.answer("Avval kanalga obuna bo'ling!", show_alert=True)
            await event.message.answer(text, reply_markup=keyboard)

        return None  # Handler zanjirini shu yerda to'xtatamiz

    async def _check_subscription(self, bot: Bot, user_id: int) -> bool:
        """
        Telegram Bot API orqali foydalanuvchining kanaldagi statusini tekshiradi.
        Bot albatta kanalda ADMIN bo'lishi shart, aks holda get_chat_member ishlamaydi.
        """
        try:
            member = await bot.get_chat_member(chat_id=self.channel_id, user_id=user_id)
        except TelegramBadRequest:
            # Bot kanalda admin emas yoki kanal ID noto'g'ri — xatoni yutmaslik uchun False qaytaramiz
            return False

        # "left" va "kicked" — obuna bo'lmagan holatlar
        return member.status not in ("left", "kicked")
