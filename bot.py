"""
bot.py
-------
Loyihaning kirish nuqtasi (entry point).

Bu yerda:
    1. Konfiguratsiya yuklanadi (.env / Railway Variables).
    2. Bot va Dispatcher obyektlari yaratiladi.
    3. Ma'lumotlar bazasi engine/session yaratiladi va jadvallar avtomatik hosil qilinadi.
    4. Middlewarelar ro'yxatdan o'tkaziladi (tartib muhim!).
    5. Handlerlar (routerlar) ulanadi.
    6. Long polling orqali bot ishga tushiriladi.

Ishga tushirish:  python bot.py
Railway'da:  Start Command = python bot.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config, load_config
from database.engine import create_db_and_tables, create_engine, create_session_maker
from handlers import routers
from handlers.admin_stats import register_admin_filter
from middlewares import DatabaseMiddleware, SubscriptionMiddleware, ThrottlingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Botni sozlab, ishga tushiradi."""
    config: Config = load_config()

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # FSM holatlari xotirada saqlanadi (MemoryStorage).
    # MUHIM: Railway'da bot qayta ishga tushsa (redeploy), FSM holatlari yo'qoladi —
    # bu odatiy holat va foydalanuvchi shunchaki /start bosishi kifoya.
    # Agar ko'p serverli (horizontal scaling) muhit kerak bo'lsa, buni RedisStorage'ga almashtirish tavsiya etiladi.
    dp = Dispatcher(storage=MemoryStorage())

    # --- Ma'lumotlar bazasi ---
    engine = create_engine(config.db.build_dsn())
    session_maker = create_session_maker(engine)
    await create_db_and_tables(engine)
    logger.info("Ma'lumotlar bazasi jadvallari tayyor.")

    # --- Middlewarelar (TARTIB MUHIM!) ---
    # 1) Throttling — eng birinchi, spamni oldindan cheklash uchun
    dp.update.middleware(ThrottlingMiddleware(min_interval=0.4))

    # 2) Database — sessiyani hamma narsadan oldin ochish kerak, chunki
    #    Subscription middleware ham bazaga murojaat qilishi mumkin
    dp.update.middleware(DatabaseMiddleware(session_maker))

    # 3) Subscription — bazadan keyin, lekin handlerlardan oldin
    dp.update.middleware(
        SubscriptionMiddleware(
            channel_id=config.bot.channel_id,
            channel_url=config.bot.channel_url,
        )
    )

    # --- config'ni barcha handlerlarga workflow_data orqali uzatamiz ---
    dp["config"] = config

    # --- Admin filtri ---
    register_admin_filter(config)

    # --- Routerlarni ulash ---
    dp.include_routers(*routers)

    # Eskirgan (bot ishlamagan vaqtdagi) update'larni tashlab yuborib, faqat yangilarini oladi
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot ishga tushdi. Polling boshlandi...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
