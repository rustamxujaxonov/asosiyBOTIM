"""
keyboards/reply.py
--------------------
Doimiy (Reply) klaviaturalar: asosiy menyu, jins tanlash, suhbat davomidagi menyu.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


# --- Matnlar (boshqa modullarda solishtirish uchun ham ishlatiladi) ---
BTN_SEARCH_ANY = "Anonim suhbatdosh qidirish 🔎"
BTN_SEARCH_FEMALE = "Qiz bola qidirish 🚺"
BTN_SEARCH_MALE = "Yigit qidirish 🚹"
BTN_MY_PROFILE = "Mening profilim 👤"
BTN_SETTINGS = "Profil sozlamalari ⚙️"

BTN_STOP_SEARCH = "Qidiruvni bekor qilish ❌"
BTN_END_CHAT = "Suhbatni yakunlash ❌"

BTN_MALE = "Yigit"
BTN_FEMALE = "Qiz"

BTN_BACK = "⬅️ Orqaga"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Ro'yxatdan o'tgan foydalanuvchi uchun asosiy menyu."""
    keyboard = [
        [KeyboardButton(text=BTN_SEARCH_ANY)],
        [KeyboardButton(text=BTN_SEARCH_FEMALE), KeyboardButton(text=BTN_SEARCH_MALE)],
        [KeyboardButton(text=BTN_MY_PROFILE), KeyboardButton(text=BTN_SETTINGS)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def searching_keyboard() -> ReplyKeyboardMarkup:
    """Foydalanuvchi navbatda turganda ko'rsatiladigan klaviatura."""
    keyboard = [[KeyboardButton(text=BTN_STOP_SEARCH)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def in_chat_keyboard() -> ReplyKeyboardMarkup:
    """Faol suhbat davomida ko'rsatiladigan klaviatura."""
    keyboard = [[KeyboardButton(text=BTN_END_CHAT)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def gender_reply_keyboard() -> ReplyKeyboardMarkup:
    """Ro'yxatdan o'tishda jins tanlash uchun reply klaviatura."""
    keyboard = [[KeyboardButton(text=BTN_MALE), KeyboardButton(text=BTN_FEMALE)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Klaviaturani vaqtincha yashirish uchun."""
    return ReplyKeyboardRemove()
