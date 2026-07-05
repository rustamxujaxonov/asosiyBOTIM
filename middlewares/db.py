"""
middlewares/db.py
--------------------
Har bir kelayotgan update (message, callback_query va h.k.) uchun
AsyncSession obyektini yaratib, handler ichiga 'session' nomi bilan uzatadi.

Bu yondashuv har bir handlerda alohida session ochish/yopishning oldini oladi
va sessiyaning to'g'ri yopilishini (transaction tugagach) kafolatlaydi.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    """Har bir update uchun yangi AsyncSession ochadi va handlerga uzatadi."""

    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
