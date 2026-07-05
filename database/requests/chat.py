"""
database/requests/chat.py
--------------------------
'active_queue' va 'active_chats' jadvallari bilan ishlash.
Bu modul suhbatdosh qidirish, ulash va suhbatni yakunlash mantig'ini o'z ichiga oladi.
"""

import random

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ActiveChat, ActiveQueue, User


async def add_to_queue(session: AsyncSession, user_id: int, search_gender: str | None) -> None:
    """Foydalanuvchini qidiruv navbatiga qo'shadi."""
    session.add(ActiveQueue(user_id=user_id, search_gender=search_gender))
    await session.commit()


async def remove_from_queue(session: AsyncSession, user_id: int) -> None:
    """Foydalanuvchini navbatdan olib tashlaydi (masalan, qidiruvni bekor qilganda)."""
    await session.execute(delete(ActiveQueue).where(ActiveQueue.user_id == user_id))
    await session.commit()


async def is_in_queue(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(ActiveQueue).where(ActiveQueue.user_id == user_id))
    return result.scalar_one_or_none() is not None


async def find_match(
    session: AsyncSession, user_id: int, my_gender: str | None, search_gender: str | None
) -> User | None:
    """
    Navbatdan mos suhbatdosh qidiradi.

    Filtrlash mantig'i:
        - Agar men (search_gender) belgilab qidirsam -> qarshi tomonning jinsi shunga mos kelishi kerak.
        - Agar qarshi tomon meni jins bo'yicha qidirayotgan bo'lsa -> mening jinsim ularning talabiga mos kelishi kerak.
        - Ikkalasi ham "tekin" (search_gender=None) bo'lsa -> jinsdan qat'iy nazar ulanadi.

    Mos nomzodlar orasidan RANDOM tarzda bittasi tanlanadi (talabga muvofiq).
    """
    query = select(ActiveQueue, User).join(User, ActiveQueue.user_id == User.id).where(
        ActiveQueue.user_id != user_id
    )
    result = await session.execute(query)
    candidates = result.all()

    suitable: list[User] = []
    for queue_entry, candidate_user in candidates:
        # 1) Mening talabim: agar men jinsni tanlab qidirsam, nomzod shu jinsda bo'lishi kerak
        if search_gender is not None:
            candidate_gender_value = (
                candidate_user.gender.value if candidate_user.gender else None
            )
            if candidate_gender_value != search_gender:
                continue

        # 2) Nomzodning talabi: agar u jinsni tanlab qidirayotgan bo'lsa, men mos kelishim kerak
        if queue_entry.search_gender is not None:
            if my_gender != queue_entry.search_gender:
                continue

        suitable.append(candidate_user)

    if not suitable:
        return None

    return random.choice(suitable)


async def create_chat_session(session: AsyncSession, user1_id: int, user2_id: int) -> None:
    """
    Ikki foydalanuvchini bog'laydi: navbatdan olib tashlab, active_chats jadvaliga yozadi.
    """
    session.add(ActiveChat(user1_id=user1_id, user2_id=user2_id))
    await session.execute(
        delete(ActiveQueue).where(ActiveQueue.user_id.in_([user1_id, user2_id]))
    )
    await session.commit()


async def get_active_partner_id(session: AsyncSession, user_id: int) -> int | None:
    """
    Foydalanuvchining hozirgi suhbatdoshi ID'sini qaytaradi.
    Agar faol suhbatda bo'lmasa — None.
    """
    query = select(ActiveChat).where(
        or_(ActiveChat.user1_id == user_id, ActiveChat.user2_id == user_id)
    )
    result = await session.execute(query)
    chat = result.scalar_one_or_none()

    if chat is None:
        return None

    return chat.user2_id if chat.user1_id == user_id else chat.user1_id


async def end_chat_session(session: AsyncSession, user_id: int) -> int | None:
    """
    Foydalanuvchining faol suhbatini tugatadi.
    Suhbatdosh ID'sini qaytaradi (unga xabar yuborish uchun), topilmasa None.
    """
    partner_id = await get_active_partner_id(session, user_id)
    if partner_id is None:
        return None

    await session.execute(
        delete(ActiveChat).where(
            or_(
                ActiveChat.user1_id == user_id,
                ActiveChat.user2_id == user_id,
            )
        )
    )
    await session.commit()
    return partner_id
