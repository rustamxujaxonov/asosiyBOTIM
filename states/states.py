"""
states/states.py
------------------
Barcha FSM (Finite State Machine) holatlari shu yerda e'lon qilinadi.
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Dastlabki ro'yxatdan o'tish jarayoni (obunadan keyin)."""
    waiting_full_name = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_region = State()


class EditProfileStates(StatesGroup):
    """
    'Profil sozlamalari' bo'limida ma'lumotlarni qayta tahrirlash.
    Har bir maydon alohida state — foydalanuvchi faqat bitta maydonni yangilaydi.
    """
    waiting_full_name = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_region = State()


class PaymentStates(StatesGroup):
    """Premium sotib olish jarayonida chek rasmini kutish."""
    waiting_receipt_photo = State()
