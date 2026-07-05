"""
handlers/settings.py
------------------------
"Profil sozlamalari ⚙️" bo'limi.

Foydalanuvchi istalgan vaqtda Ism, Yosh, Jins yoki Viloyatini
alohida-alohida qayta o'zgartirishi mumkin (har biri mustaqil FSM oqimi).
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenderEnum
from database.requests import update_age, update_full_name, update_gender, update_region
from keyboards.inline import (
    EditGenderCallback,
    EditProfileCallback,
    RegionCallback,
    edit_gender_keyboard,
    region_keyboard,
    settings_menu_keyboard,
)
from keyboards.reply import BTN_SETTINGS, main_menu_keyboard
from states.states import EditProfileStates

router = Router(name="settings")

MIN_AGE = 13
MAX_AGE = 99


@router.message(lambda m: m.text == BTN_SETTINGS)
async def open_settings(message: Message, state: FSMContext) -> None:
    """Sozlamalar menyusini ochadi."""
    await state.clear()
    await message.answer(
        "⚙️ Profil sozlamalari.\n\nQaysi ma'lumotni o'zgartirmoqchisiz?",
        reply_markup=settings_menu_keyboard(),
    )


@router.callback_query(EditProfileCallback.filter())
async def choose_field_to_edit(
    callback: CallbackQuery, callback_data: EditProfileCallback, state: FSMContext
) -> None:
    """Foydalanuvchi qaysi maydonni tahrirlamoqchi ekanini tanlaganda mos state'ni yoqadi."""
    field = callback_data.field
    await callback.answer()

    if field == "full_name":
        await callback.message.edit_text("✏️ Yangi ismingizni kiriting:")
        await state.set_state(EditProfileStates.waiting_full_name)

    elif field == "age":
        await callback.message.edit_text("🎂 Yangi yoshingizni kiriting (raqamda):")
        await state.set_state(EditProfileStates.waiting_age)

    elif field == "gender":
        await callback.message.edit_text("⚧ Yangi jinsingizni tanlang:", reply_markup=edit_gender_keyboard())
        await state.set_state(EditProfileStates.waiting_gender)

    elif field == "region":
        await callback.message.edit_text("📍 Yangi viloyatingizni tanlang:", reply_markup=region_keyboard(RegionCallback))
        await state.set_state(EditProfileStates.waiting_region)


@router.message(EditProfileStates.waiting_full_name)
async def edit_full_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    full_name = (message.text or "").strip()

    if not full_name or len(full_name) < 2 or len(full_name) > 64:
        await message.answer("⚠️ Iltimos, to'g'ri ism kiriting (2-64 belgi).")
        return

    await update_full_name(session, message.from_user.id, full_name)
    await state.clear()
    await message.answer(f"✅ Ismingiz \"{full_name}\" ga muvaffaqiyatli o'zgartirildi.", reply_markup=main_menu_keyboard())


@router.message(EditProfileStates.waiting_age)
async def edit_age(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()

    if not text.isdigit() or not (MIN_AGE <= int(text) <= MAX_AGE):
        await message.answer(f"⚠️ Iltimos, {MIN_AGE}-{MAX_AGE} oralig'ida haqiqiy yoshingizni kiriting.")
        return

    await update_age(session, message.from_user.id, int(text))
    await state.clear()
    await message.answer(f"✅ Yoshingiz {text} ga muvaffaqiyatli o'zgartirildi.", reply_markup=main_menu_keyboard())


@router.callback_query(EditProfileStates.waiting_gender, EditGenderCallback.filter())
async def edit_gender(
    callback: CallbackQuery, callback_data: EditGenderCallback, state: FSMContext, session: AsyncSession
) -> None:
    await update_gender(session, callback.from_user.id, GenderEnum(callback_data.gender))
    await state.clear()

    await callback.answer("✅ Jinsingiz o'zgartirildi!")
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Jinsingiz \"{callback_data.gender}\" ga muvaffaqiyatli o'zgartirildi.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(EditProfileStates.waiting_region, RegionCallback.filter())
async def edit_region(
    callback: CallbackQuery, callback_data: RegionCallback, state: FSMContext, session: AsyncSession
) -> None:
    await update_region(session, callback.from_user.id, callback_data.name)
    await state.clear()

    await callback.answer("✅ Viloyatingiz o'zgartirildi!")
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Viloyatingiz \"{callback_data.name}\" ga muvaffaqiyatli o'zgartirildi.",
        reply_markup=main_menu_keyboard(),
    )
