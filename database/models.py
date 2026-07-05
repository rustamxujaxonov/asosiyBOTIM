"""
database/models.py
-------------------
Loyihaning barcha SQLAlchemy ORM (asinxron) modellari shu yerda e'lon qilinadi.

Jadvallar:
    - users            : Har bir foydalanuvchi profili
    - active_queue      : "Suhbatdosh qidirilmoqda" navbatidagi foydalanuvchilar
    - active_chats       : Hozirda bir-biri bilan bog'langan (suhbatlashayotgan) juftliklar
    - payment_requests   : Premium sotib olish uchun yuborilgan cheklar (admin tasdig'i kutilmoqda)
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Barcha modellar uchun umumiy asos klass."""
    pass


class GenderEnum(str, enum.Enum):
    """Foydalanuvchi jinsi."""
    MALE = "yigit"
    FEMALE = "qiz"


class PackageEnum(str, enum.Enum):
    """Premium paket turlari (kunlar soniga mos)."""
    DAY_1 = "1_kunlik"
    DAY_3 = "3_kunlik"
    WEEK_1 = "1_haftalik"
    MONTH_1 = "1_oylik"
    REFERRAL_BONUS = "referal_bonus"


class PaymentStatusEnum(str, enum.Enum):
    """To'lov holati."""
    PENDING = "kutilmoqda"
    APPROVED = "tasdiqlandi"
    REJECTED = "rad_etildi"


# Har bir paketga mos kunlar soni (handlerlarda muddatni hisoblash uchun ishlatiladi)
PACKAGE_DAYS: dict[str, int] = {
    PackageEnum.DAY_1.value: 1,
    PackageEnum.DAY_3.value: 3,
    PackageEnum.WEEK_1.value: 7,
    PackageEnum.MONTH_1.value: 30,
    PackageEnum.REFERRAL_BONUS.value: 2,
}

# Har bir paketning narxi (so'mda) — inline tugmalarda va admin xabarida ko'rsatish uchun
PACKAGE_PRICES: dict[str, int] = {
    PackageEnum.DAY_1.value: 5_000,
    PackageEnum.DAY_3.value: 10_000,
    PackageEnum.WEEK_1.value: 20_000,
    PackageEnum.MONTH_1.value: 30_000,
}

# Foydalanuvchiga chiroyli ko'rsatish uchun paket nomlari
PACKAGE_LABELS: dict[str, str] = {
    PackageEnum.DAY_1.value: "1 kunlik",
    PackageEnum.DAY_3.value: "3 kunlik",
    PackageEnum.WEEK_1.value: "1 haftalik",
    PackageEnum.MONTH_1.value: "1 oylik",
}


class User(Base):
    """Foydalanuvchi profili jadvali."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[GenderEnum | None] = mapped_column(Enum(GenderEnum), nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)

    premium_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Referal tizimi
    referrer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    invited_count: Mapped[int] = mapped_column(Integer, default=0)
    referral_bonus_claimed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def is_premium(self) -> bool:
        """Foydalanuvchi hozirda Premium ekanligini tekshiradi."""
        if self.premium_until is None:
            return False
        return self.premium_until > datetime.utcnow()


class ActiveQueue(Base):
    """
    'Suhbatdosh qidirilmoqda' navbati.
    Foydalanuvchi tugma bosganda shu jadvalga qo'shiladi va juft topilishi kutiladi.
    """

    __tablename__ = "active_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )

    # search_gender: qidirilayotgan jins filtri.
    #   None  -> "Anonim suhbatdosh qidirish" (tekin, jins muhim emas)
    #   "qiz" / "yigit" -> Premium filtrlangan qidiruv
    search_gender: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ActiveChat(Base):
    """
    Ikki foydalanuvchi bog'langandan keyingi faol suhbat sessiyasi.
    Har bir suhbat uchun bitta qator, ikkala tomon ham shu qatorni ko'radi.
    """

    __tablename__ = "active_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user2_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PaymentRequest(Base):
    """
    Foydalanuvchi yuborgan to'lov cheki va uning holati.
    Admin guruhida "Tasdiqlash / Rad etish" tugmalari shu yozuv ID'siga bog'lanadi.
    """

    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    package: Mapped[str] = mapped_column(String(32), nullable=False)  # PackageEnum qiymati
    amount: Mapped[int] = mapped_column(Integer, nullable=False)      # narx (so'm)

    photo_file_id: Mapped[str] = mapped_column(String(256), nullable=False)  # chek rasmi (Telegram file_id)

    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING
    )

    admin_group_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
