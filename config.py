"""
config.py
----------
Loyihaning markaziy konfiguratsiya moduli.
Barcha maxfiy va muhim sozlamalar (.env) fayldan o'qiladi.
Railway platformasida bu qiymatlar "Variables" bo'limida beriladi.
"""

from dataclasses import dataclass
from environs import Env


@dataclass
class BotConfig:
    """Botga oid asosiy sozlamalar."""
    token: str
    admin_ids: list[int]
    admin_group_id: int
    channel_id: str          # Majburiy obuna kanali (masalan: @kanal_username yoki -100xxxxxxxxxx)
    channel_url: str         # Foydalanuvchi bosishi uchun havola (masalan: https://t.me/kanal_username)
    bot_username: str        # Referal havola yasash uchun (masalan: TanishuvlarBOT, @ belgisisiz)


@dataclass
class DatabaseConfig:
    """PostgreSQL ma'lumotlar bazasiga ulanish sozlamalari (Railway)."""
    host: str
    port: int
    password: str
    user: str
    database: str

    def build_dsn(self) -> str:
        """SQLAlchemy async (asyncpg) uchun DSN satrini yasaydi."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class PaymentConfig:
    """To'lov (P2P karta) uchun ma'lumotlar."""
    card_number: str
    card_owner: str


@dataclass
class Config:
    bot: BotConfig
    db: DatabaseConfig
    payment: PaymentConfig


def load_config(path: str | None = None) -> Config:
    """
    .env faylidan barcha sozlamalarni o'qib, Config obyektini qaytaradi.
    Railway'da bu o'zgaruvchilar avtomatik muhitga (environment) inject qilinadi,
    shuning uchun path=None bo'lsa ham environs .env bo'lmasa xatolik bermaydi
    (Railway'da .env fayli shart emas, o'zgaruvchilar to'g'ridan-to'g'ri beriladi).
    """
    env = Env()
    env.read_env(path)  # Agar .env fayli mavjud bo'lmasa ham xato bermaydi (lokal test uchun)

    return Config(
        bot=BotConfig(
            token=env.str("BOT_TOKEN"),
            admin_ids=[int(x) for x in env.list("ADMIN_IDS", default=[])],
            admin_group_id=env.int("ADMIN_GROUP_ID"),
            channel_id=env.str("CHANNEL_ID"),
            channel_url=env.str("CHANNEL_URL"),
            bot_username=env.str("BOT_USERNAME"),
        ),
        db=DatabaseConfig(
            host=env.str("PGHOST"),
            port=env.int("PGPORT", 5432),
            password=env.str("PGPASSWORD"),
            user=env.str("PGUSER"),
            database=env.str("PGDATABASE"),
        ),
        payment=PaymentConfig(
            card_number=env.str("CARD_NUMBER"),
            card_owner=env.str("CARD_OWNER"),
        ),
    )
