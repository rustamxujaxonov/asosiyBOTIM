"""
handlers/registration.py
----------------------------
Dastlabki ro'yxatdan o'tish jarayoni (FSM):
    Ism -> Yosh -> Jins -> Viloyat -> Bazaga saqlash -> Asosiy menyu.

Referal bonus tekshiruvi ham shu yerda, ro'yxatdan o'tish yakunida amalga oshiriladi
(chunki referal "chaqirilgan do'st" faqat to'liq ro'yxatdan o'tgandagina hisobga olinadi).
"""

from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.models import GenderEnum, PACKAGE_DAYS, PackageEnum
from database.requests import (
    extend_premium,
    get_user,
    increment_invited_count,
    mark_referral_bonus_claimed,
    update_registration,
)
from keyboards.inline import RegionCallback, region_keyboard
from keyboards.reply import (
    BTN_FEMALE,
    BTN_MALE,
    gender_reply_keyboard,
    main_menu_keyboard,
    remove_keyboard,
)
from states.states import RegistrationStates

router = Router(name="registration")

MIN_AGE = 13
MAX_AGE = 99
REFERRAL_TARGET_COUNT = 5


@router.message(RegistrationStates.waiting_full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    """Ism kiritilgandan keyin yoshni so'raydi."""
    full_name = (message.text or "").strip()

    if not full_name or len(full_name) < 2 or len(full_name) > 64:
        await message.answer(
            "⚠️ Iltimos, to'g'ri ism kiriting (2-64 belgi oralig'ida, faqat matn)."
        )
        return

    await state.update_data(full_name=full_name)
    await message.answer(f"Rahmat, {full_name}! 🎂 Endi yoshingizni kiriting (raqamda, masalan: 21):")
    await state.set_state(RegistrationStates.waiting_age)


@router.message(RegistrationStates.waiting_age)
async def process_age(message: Message, state: FSMContext) -> None:
    """Yosh kiritilgandan keyin jinsni so'raydi."""
    text = (message.text or "").strip()

    if not text.isdigit() or not (MIN_AGE <= int(text) <= MAX_AGE):
        await message.answer(
            f"⚠️ Iltimos, {MIN_AGE} dan {MAX_AGE} gacha bo'lgan haqiqiy yoshingizni raqamda kiriting."
        )
        return

    await state.update_data(age=int(text))
    await message.answer(
        "Jinsingizni tanlang:",
        reply_markup=gender_reply_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_gender)


@router.message(RegistrationStates.waiting_gender)
async def process_gender(message: Message, state: FSMContext) -> None:
    """Jins tanlangandan keyin viloyatni so'raydi (inline klaviatura orqali)."""
    text = (message.text or "").strip()

    gender_map = {BTN_MALE: GenderEnum.MALE, BTN_FEMALE: GenderEnum.FEMALE}
    if text not in gender_map:
        await message.answer(
            "⚠️ Iltimos, quyidagi tugmalardan birini tanlang.",
            reply_markup=gender_reply_keyboard(),
        )
        return

    await state.update_data(gender=gender_map[text].value)
    await message.answer(
        "Viloyatingizni tanlang:",
        reply_markup=remove_keyboard(),
    )
    await message.answer("👇", reply_markup=region_keyboard(RegionCallback))
    await state.set_state(RegistrationStates.waiting_region)


@router.callback_query(RegistrationStates.waiting_region, RegionCallback.filter())
async def process_region(
    callback,
    callback_data: RegionCallback,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    config: Config,
) -> None:
    """
    Viloyat tanlangandan so'ng barcha ma'lumotlarni bazaga saqlaydi,
    referal bonusni tekshiradi va foydalanuvchini asosiy menyuga yo'naltiradi.
    """
    data = await state.get_data()

    await update_registration(
        session=session,
        user_id=callback.from_user.id,
        full_name=data["full_name"],
        age=data["age"],
        gender=GenderEnum(data["gender"]),
        region=callback_data.name,
    )
    await state.clear()

    await callback.message.delete()
    await callback.answer("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!")
    await callback.message.answer(
        "🎉 Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(),
    )

    # --- Referal bonusni tekshirish ---
    new_user = await get_user(session, callback.from_user.id)
    if new_user and new_user.referrer_id:
        await _process_referral_bonus(
            session=session, referrer_id=new_user.referrer_id, bot=bot
        )


async def _process_referral_bonus(session: AsyncSession, referrer_id: int, bot: Bot) -> None:
    """
    Referrer'ning taklif qilganlar sonini oshiradi.
    Agar 5 taga yetgan bo'lsa va bonus hali berilmagan bo'lsa — 2 kunlik Premium beradi.
    """
    new_count = await increment_invited_count(session, referrer_id)

    referrer = await get_user(session, referrer_id)
    if referrer is None:
        return

    if new_count >= REFERRAL_TARGET_COUNT and not referrer.referral_bonus_claimed:
        premium_until = await extend_premium(
            session, referrer_id, PACKAGE_DAYS[PackageEnum.REFERRAL_BONUS.value]
        )
        await mark_referral_bonus_claimed(session, referrer_id)

        try:
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎁 Tabriklaymiz! Siz 5 ta do'stingizni taklif qildingiz va "
                    "avtomatik ravishda 2 kunlik Premium qo'lga kiritdingiz!\n\n"
                    f"Premium muddati: {premium_until.strftime('%Y-%m-%d %H:%M')} gacha."
                ),
            )
        except Exception:
            # Foydalanuvchi botni bloklagan bo'lishi mumkin — bu bonusni bekor qilmaydi
            pass
