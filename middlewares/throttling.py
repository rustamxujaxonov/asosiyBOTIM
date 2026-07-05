"""
middlewares/throttling.py
---------------------------
Oddiy anti-flood (throttling) middleware.

Foydalanuvchi bir necha soniya ichida ko'p marta xabar yuborsa
(masalan, suhbat davomida tez-tez bosilsa), ortiqcha yukni kamaytirish uchun
juda tez-tez kelgan so'rovlarni e'tiborsiz qoldiradi.

Production muhitida buning o'rniga Redis-based throttling (masalan,
aiogram-dan cachetools yoki aiogram_dialog throttling) ishlatish tavsiya etiladi,
ammo bitta-server Railway deploy uchun in-memory yechim yetarli.
"""

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Foydalanuvchi so'rovlari orasidagi minimal vaqt oralig'ini nazorat qiladi."""

    def __init__(self, min_interval: float = 0.5):
        self.min_interval = min_interval
        self._last_call: dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_call.get(user.id, 0.0)

        if now - last < self.min_interval:
            # Juda tez-tez kelgan so'rovni jimgina e'tiborsiz qoldiramiz
            return None

        self._last_call[user.id] = now
        return await handler(event, data)
