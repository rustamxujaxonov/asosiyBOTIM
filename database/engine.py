"""
database/engine.py
-------------------
Asinxron SQLAlchemy engine va session fabrikasini yaratadi.
asyncpg drayveri orqali PostgreSQL (Railway) bilan ishlaydi.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.models import Base


def create_engine(dsn: str) -> AsyncEngine:
    """
    Berilgan DSN asosida asinxron SQLAlchemy engine yaratadi.

    pool_pre_ping=True — Railway kabi bulutli muhitlarda uzilib qolgan
    ulanishlarni avtomatik tekshirib, yangilaydi (Connection reset xatolarining oldini oladi).
    """
    engine = create_async_engine(
        dsn,
        echo=False,          # Debug vaqtida True qilib SQL so'rovlarni ko'rish mumkin
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    return engine


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Har bir so'rov uchun yangi AsyncSession yaratadigan fabrika."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,   # commit'dan keyin obyekt atributlariga kirishda xato bo'lmasligi uchun
        autoflush=False,
    )


async def create_db_and_tables(engine: AsyncEngine) -> None:
    """
    Loyihadagi barcha models.py'da e'lon qilingan jadvallarni
    ma'lumotlar bazasida yaratadi (agar mavjud bo'lmasa).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
