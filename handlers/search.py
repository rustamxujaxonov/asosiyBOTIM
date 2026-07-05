"""
handlers/search.py
----------------------
Suhbatdosh qidirish tugmalari:
    - "Anonim suhbatdosh qidirish 🔎"  (tekin, jinsdan qat'iy nazar)
    - "Qiz bola qidirish 🚺"           (Premium talab qiladi)
    - "Yigit qidirish 🚹"              (Premium talab qiladi)

Agar foydalanuvchi Premium bo'lmasa va jinsli qidiruvni tanlasa —
premium_prompt.py orqali paketlar ko'rsatiladi (bu yerda faqat yo'naltirish qilinadi).

Agar shartlar bajarilsa, foydalanuvchi navbatga qo'shiladi va mos judet qidiriladi.
Juftlik topilsa — ikkalasiga ham suhbat boshlanganligi haqida xabar boradi.
"""

from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import (
    add_to_queue,
    create_chat_session,
    find_match,
    get_user,
    is_in_queue,
    remove_from_queue,
)
from keyboards.reply import (
    BTN_SEARCH_ANY,
    BTN_SEARCH_FEMALE,
    BTN_SEARCH_MALE,
    BTN_STOP_SEARCH,
    in_chat_keyboard,
    main_menu_keyboard,
    searching_keyboard,
)

router = Router(name="search")


@router.message(lambda m: m.text == BTN_SEARCH_ANY)
async def search_any(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    """Tekin, jinsdan qat'iy nazar suhbatdosh qidirish."""
    await _start_search(message, state, session, bot, search_gender=None)


@router.message(lambda m: m.text == BTN_SEARCH_FEMALE)
async def search_female(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    """Qiz bola qidirish (Premium talab qiladi)."""
    await _handle_premium_search(message, state, session, bot, target_gender="qiz")


@router.message(lambda m: m.text == BTN_SEARCH_MALE)
async def search_male(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    """Yigit qidirish (Premium talab qiladi)."""
    await _handle_premium_search(message, state, session, bot, target_gender="yigit")


@router.message(lambda m: m.text == BTN_STOP_SEARCH)
async def stop_search(message: Message, session: AsyncSession) -> None:
    """Foydalanuvchi qidiruvni navbatdan chiqib bekor qiladi."""
    await remove_from_queue(session, message.from_user.id)
    await message.answer("Qidiruv bekor qilindi.", reply_markup=main_menu_keyboard())


async def _handle_premium_search(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot, target_gender: str
) -> None:
    """Premium talab qiluvchi qidiruvlar uchun umumiy tekshiruv."""
    user = await get_user(session, message.from_user.id)

    if not user or not user.is_registered:
        await message.answer("⚠️ Iltimos, avval /start orqali ro'yxatdan o'ting.")
        return

    if not user.is_premium():
        # Premium taklifini ko'rsatish uchun premium_prompt modulidagi funksiyani chaqiramiz.
        # Aylanma import'ning oldini olish uchun funksiya ichida import qilamiz.
        from handlers.premium_prompt import show_premium_offer

        await show_premium_offer(message, target_gender=target_gender)
        return

    await _start_search(message, state, session, bot, search_gender=target_gender)


async def _start_search(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    search_gender: str | None,
) -> None:
    """
    Umumiy qidiruv logikasi: navbatga qo'shish, mos judet qidirish,
    topilsa ikkala tomonni ham bog'lash va xabar berish.
    """
    user_id = message.from_user.id

    user = await get_user(session, user_id)
    if not user or not user.is_registered:
        await message.answer("⚠️ Iltimos, avval /start orqali ro'yxatdan o'ting.")
        return

    already_searching = await is_in_queue(session, user_id)
    if already_searching:
        await message.answer("⏳ Siz allaqachon qidiruvdasiz. Iltimos, kuting...")
        return

    my_gender = user.gender.value if user.gender else None

    partner = await find_match(session, user_id, my_gender=my_gender, search_gender=search_gender)

    if partner is None:
        # Mos judet topilmadi -> navbatga qo'shamiz va kutamiz
        await add_to_queue(session, user_id, search_gender)
        await message.answer(
            "🔎 Suhbatdosh qidirilmoqda...\n\nIltimos, biroz kuting yoki qidiruvni bekor qiling.",
            reply_markup=searching_keyboard(),
        )
        return

    # Mos judet topildi -> ikkalasini bog'laymiz
    await create_chat_session(session, user_id, partner.id)

    await _notify_chat_started(bot, session, user_id=user_id, partner_id=partner.id)
    await _notify_chat_started(bot, session, user_id=partner.id, partner_id=user_id)


async def _notify_chat_started(bot: Bot, session: AsyncSession, user_id: int, partner_id: int) -> None:
    """
    Suhbat boshlanganini foydalanuvchiga bildiradi.
    Agar foydalanuvchi Premium bo'lsa, suhbatdoshining jinsi/yoshi/viloyatini ham ko'rsatadi.
    """
    viewer = await get_user(session, user_id)
    partner = await get_user(session, partner_id)

    text = "✅ Suhbatdosh topildi! Endi anonim tarzda yozishingiz mumkin.\n\n"

    if viewer.is_premium():
        gender_display = "Yigit 🚹" if partner.gender and partner.gender.value == "yigit" else "Qiz 🚺"
        text += (
            f"ℹ️ Suhbatdoshingiz haqida (Premium):\n"
            f"⚧ Jins: {gender_display}\n"
            f"🎂 Yosh: {partner.age}\n"
            f"📍 Viloyat: {partner.region}\n\n"
        )

    text += "Suhbatni yakunlash uchun pastdagi tugmani bosing."

    try:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=in_chat_keyboard())
    except Exception:
        # Foydalanuvchi botni bloklagan bo'lishi mumkin
        pass
