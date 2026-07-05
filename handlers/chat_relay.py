"""
handlers/chat_relay.py
--------------------------
Faol suhbat davomidagi xabar almashish (relay) logikasi.

Foydalanuvchi suhbatda bo'lsa, uning yuborgan HAR QANDAY turdagi xabari
(matn, rasm, video, ovozli xabar, sticker, hujjat va h.k.) suhbatdoshiga
copy_message orqali ANONIM tarzda (jo'natuvchi ismi ko'rinmasdan) yetkaziladi.

MUHIM: Bu router registratsiya tartibida boshqa "asosiy menyu tugmalari"
handlerlaridan KEYIN, lekin registratsiya/premium kabi state talab qilmaydigan
oddiy xabarlar handlerlaridan oldin turishi kerak (dispatcher.py'da tartib muhim).
Aslida buni middleware orqali ham hal qilish mumkin, lekin oddiylik uchun
bu yerda navbatning oxirida joylashgan "catch-all" filter sifatida ishlatamiz.
"""

from aiogram import Bot, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import end_chat_session, get_active_partner_id
from keyboards.reply import BTN_END_CHAT, main_menu_keyboard

router = Router(name="chat_relay")


@router.message(lambda m: m.text == BTN_END_CHAT)
async def end_chat(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Foydalanuvchi 'Suhbatni yakunlash' tugmasini bosganda ishlaydi."""
    partner_id = await end_chat_session(session, message.from_user.id)

    if partner_id is None:
        await message.answer("Siz hozir hech kim bilan suhbatlashmayapsiz.", reply_markup=main_menu_keyboard())
        return

    await message.answer("❌ Suhbat yakunlandi.", reply_markup=main_menu_keyboard())

    try:
        await bot.send_message(
            chat_id=partner_id,
            text="❌ Suhbatdoshingiz suhbatni yakunladi.",
            reply_markup=main_menu_keyboard(),
        )
    except Exception:
        # Suhbatdosh botni bloklagan bo'lishi mumkin
        pass


@router.message()
async def relay_message(message: Message, session: AsyncSession, bot: Bot) -> None:
    """
    Boshqa hech qanday handlerga mos kelmagan barcha xabarlarni ushlaydi.
    Agar foydalanuvchi faol suhbatda bo'lsa — xabarni suhbatdoshga anonim ravishda yuboradi.
    Aks holda — asosiy menyudan foydalanishni so'raydi.
    """
    partner_id = await get_active_partner_id(session, message.from_user.id)

    if partner_id is None:
        await message.answer(
            "Iltimos, quyidagi menyudan kerakli bo'limni tanlang.",
            reply_markup=main_menu_keyboard(),
        )
        return

    try:
        # copy_message — xabarni "asl jo'natuvchi" ko'rinishisiz nusxalab yuboradi,
        # shu tufayli anonimlik ta'minlanadi (forward_message'dan farqli o'laroq).
        await bot.copy_message(
            chat_id=partner_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception:
        await message.answer(
            "⚠️ Xabar yuborilmadi. Suhbatdoshingiz botni bloklagan bo'lishi mumkin."
        )
