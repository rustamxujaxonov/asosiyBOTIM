"""
database/requests/users.py
---------------------------
'users' jadvali bilan ishlash uchun barcha funksiyalar (CRUD).
Har bir funksiya AsyncSession'ni parametr sifatida qabul qiladi
(session middleware orqali handlerlarga uzatiladi).
"""

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenderEnum, User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """user_id bo'yicha foydalanuvchini qaytaradi (topilmasa None)."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: str | None,
    referrer_id: int | None = None,
) -> tuple[User, bool]:
    """
    Foydalanuvchini bazadan qidiradi, topilmasa yangisini yaratadi.
    Qaytaradi: (User obyekti, yangi_yaratildimi: bool)
    """
    user = await get_user(session, user_id)
    if user:
        # Username o'zgargan bo'lishi mumkin — yangilab qo'yamiz
        if username and user.username != username:
            user.username = username
            await session.commit()
        return user, False

    # Agar referrer o'zi-o'ziga taklif bermoqchi bo'lsa (start=own_id), bepul bekor qilamiz
    if referrer_id == user_id:
        referrer_id = None

    new_user = User(
        id=user_id,
        username=username,
        is_registered=False,
        referrer_id=referrer_id,
    )
    session.add(new_user)
    await session.commit()
    return new_user, True


async def update_registration(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    age: int,
    gender: GenderEnum,
    region: str,
) -> None:
    """Ro'yxatdan o'tish (yoki profilni tahrirlash) ma'lumotlarini saqlaydi."""
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            full_name=full_name,
            age=age,
            gender=gender,
            region=region,
            is_registered=True,
        )
    )
    await session.commit()


async def update_full_name(session: AsyncSession, user_id: int, full_name: str) -> None:
    await session.execute(update(User).where(User.id == user_id).values(full_name=full_name))
    await session.commit()


async def update_age(session: AsyncSession, user_id: int, age: int) -> None:
    await session.execute(update(User).where(User.id == user_id).values(age=age))
    await session.commit()


async def update_gender(session: AsyncSession, user_id: int, gender: GenderEnum) -> None:
    await session.execute(update(User).where(User.id == user_id).values(gender=gender))
    await session.commit()


async def update_region(session: AsyncSession, user_id: int, region: str) -> None:
    await session.execute(update(User).where(User.id == user_id).values(region=region))
    await session.commit()


async def extend_premium(session: AsyncSession, user_id: int, days: int) -> datetime:
    """
    Foydalanuvchi Premium muddatini uzaytiradi.
    Agar hozir ham Premium bo'lsa — mavjud muddatga qo'shiladi (stacking).
    Agar Premium tugagan yoki umuman bo'lmagan bo'lsa — hozirgi vaqtdan boshlab hisoblanadi.
    Yangi premium_until sanasini qaytaradi.
    """
    user = await get_user(session, user_id)
    now = datetime.utcnow()

    base_time = user.premium_until if (user.premium_until and user.premium_until > now) else now
    new_until = base_time + timedelta(days=days)

    await session.execute(
        update(User).where(User.id == user_id).values(premium_until=new_until)
    )
    await session.commit()
    return new_until


async def increment_invited_count(session: AsyncSession, referrer_id: int) -> int:
    """
    Referrer'ning taklif qilgan do'stlar sonini 1 taga oshiradi.
    Yangilangan invited_count qiymatini qaytaradi.
    """
    referrer = await get_user(session, referrer_id)
    if referrer is None:
        return 0

    new_count = referrer.invited_count + 1
    await session.execute(
        update(User).where(User.id == referrer_id).values(invited_count=new_count)
    )
    await session.commit()
    return new_count


async def mark_referral_bonus_claimed(session: AsyncSession, user_id: int) -> None:
    """5 ta referal uchun bonus allaqachon berilganini belgilaydi (qayta bermaslik uchun)."""
    await session.execute(
        update(User).where(User.id == user_id).values(referral_bonus_claimed=True)
    )
    await session.commit()
