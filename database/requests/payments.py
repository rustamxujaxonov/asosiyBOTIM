"""
database/requests/payments.py
------------------------------
'payment_requests' jadvali bilan ishlash: chek yaratish, admin tasdig'ini yozish.
"""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PaymentRequest, PaymentStatusEnum


async def create_payment_request(
    session: AsyncSession,
    user_id: int,
    package: str,
    amount: int,
    photo_file_id: str,
) -> PaymentRequest:
    """Yangi to'lov (chek) so'rovini yaratadi va uni qaytaradi (id kerak bo'ladi)."""
    payment = PaymentRequest(
        user_id=user_id,
        package=package,
        amount=amount,
        photo_file_id=photo_file_id,
        status=PaymentStatusEnum.PENDING,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def set_admin_message_id(session: AsyncSession, payment_id: int, message_id: int) -> None:
    """Admin guruhiga yuborilgan xabar ID'sini saqlaydi (keyinchalik tugmani yangilash uchun)."""
    await session.execute(
        update(PaymentRequest)
        .where(PaymentRequest.id == payment_id)
        .values(admin_group_message_id=message_id)
    )
    await session.commit()


async def get_payment_request(session: AsyncSession, payment_id: int) -> PaymentRequest | None:
    result = await session.execute(
        select(PaymentRequest).where(PaymentRequest.id == payment_id)
    )
    return result.scalar_one_or_none()


async def resolve_payment_request(
    session: AsyncSession, payment_id: int, status: PaymentStatusEnum
) -> None:
    """To'lov so'rovi holatini yangilaydi (tasdiqlandi / rad etildi)."""
    await session.execute(
        update(PaymentRequest)
        .where(PaymentRequest.id == payment_id)
        .values(status=status, resolved_at=datetime.utcnow())
    )
    await session.commit()
