"""
keyboards/inline.py
---------------------
Barcha inline klaviaturalar: majburiy obuna, viloyat tanlash,
Premium paketlar, admin tasdiqlash tugmalari, sozlamalar menyusi.
"""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import PACKAGE_LABELS, PACKAGE_PRICES


# =========================================================
#                  CALLBACK DATA FABRIKALARI
# =========================================================

class CheckSubscription(CallbackData, prefix="check_sub"):
    """Majburiy obunani tekshirish tugmasi uchun."""
    pass


class RegionCallback(CallbackData, prefix="region"):
    """Viloyat tanlash uchun."""
    name: str


class BuyPackageCallback(CallbackData, prefix="buy_pkg"):
    """Premium paket tanlash uchun (qaysi jinsni qidirish uchun sotib olinayotgani ham saqlanadi)."""
    package: str
    target_gender: str  # "qiz" yoki "yigit" — to'lovdan keyin qaysi qidiruvni boshlash uchun


class ReferralInfoCallback(CallbackData, prefix="ref_info"):
    """'Referal link orqali premium olish' tugmasi."""
    pass


class AdminApprovePayment(CallbackData, prefix="admin_ok"):
    """Admin guruhida 'Tasdiqlash' tugmasi."""
    payment_id: int


class AdminRejectPayment(CallbackData, prefix="admin_no"):
    """Admin guruhida 'Rad etish' tugmasi."""
    payment_id: int


class EditProfileCallback(CallbackData, prefix="edit_prof"):
    """'Profil sozlamalari' bo'limidagi tanlovlar."""
    field: str  # "full_name" | "age" | "gender" | "region"


class EditGenderCallback(CallbackData, prefix="edit_gender"):
    """Profilni tahrirlashda yangi jins tanlash."""
    gender: str


# =========================================================
#                     VILOYATLAR RO'YXATI
# =========================================================

UZBEKISTAN_REGIONS: list[str] = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Andijon",
    "Farg'ona",
    "Namangan",
    "Samarqand",
    "Buxoro",
    "Navoiy",
    "Qashqadaryo",
    "Surxondaryo",
    "Jizzax",
    "Sirdaryo",
    "Xorazm",
    "Qoraqalpog'iston",
]


# =========================================================
#                        KLAVIATURALAR
# =========================================================

def subscription_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    """Majburiy obuna: kanal havolasi + tekshirish tugmasi."""
    buttons = [
        [InlineKeyboardButton(text="📢 Kanalga o'tish", url=channel_url)],
        [
            InlineKeyboardButton(
                text="✅ Obunani tekshirish",
                callback_data=CheckSubscription().pack(),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def region_keyboard(callback_prefix: type[CallbackData] = RegionCallback) -> InlineKeyboardMarkup:
    """
    Viloyatlar ro'yxatini 2 ustunli inline klaviatura sifatida qaytaradi.
    callback_prefix orqali bitta funksiyani ro'yxatdan o'tish va tahrirlash uchun ham ishlatamiz.
    """
    buttons = []
    row = []
    for i, region in enumerate(UZBEKISTAN_REGIONS, start=1):
        row.append(
            InlineKeyboardButton(text=region, callback_data=callback_prefix(name=region).pack())
        )
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_packages_keyboard(target_gender: str) -> InlineKeyboardMarkup:
    """
    Premium paketlar ro'yxati (narxlari bilan) + referal tugmasi.
    target_gender: foydalanuvchi keyin qaysi jinsni qidirmoqchi ekanini bildiradi ("qiz"/"yigit").
    """
    buttons = []
    for package_key, label in PACKAGE_LABELS.items():
        price = PACKAGE_PRICES[package_key]
        text = f"{label} — {price:,} so'm".replace(",", " ")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=BuyPackageCallback(
                        package=package_key, target_gender=target_gender
                    ).pack(),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Referal link orqali premium olish 🎁",
                callback_data=ReferralInfoCallback().pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    """Admin guruhidagi chek xabari ostidagi 'Tasdiqlash / Rad etish' tugmalari."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=AdminApprovePayment(payment_id=payment_id).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=AdminRejectPayment(payment_id=payment_id).pack(),
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settings_menu_keyboard() -> InlineKeyboardMarkup:
    """'Profil sozlamalari' bo'limidagi maydonlar ro'yxati."""
    buttons = [
        [InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data=EditProfileCallback(field="full_name").pack())],
        [InlineKeyboardButton(text="🎂 Yoshni o'zgartirish", callback_data=EditProfileCallback(field="age").pack())],
        [InlineKeyboardButton(text="⚧ Jinsni o'zgartirish", callback_data=EditProfileCallback(field="gender").pack())],
        [InlineKeyboardButton(text="📍 Viloyatni o'zgartirish", callback_data=EditProfileCallback(field="region").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_gender_keyboard() -> InlineKeyboardMarkup:
    """Profilni tahrirlashda jins tanlash (inline formatda)."""
    buttons = [
        [
            InlineKeyboardButton(text="Yigit", callback_data=EditGenderCallback(gender="yigit").pack()),
            InlineKeyboardButton(text="Qiz", callback_data=EditGenderCallback(gender="qiz").pack()),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
