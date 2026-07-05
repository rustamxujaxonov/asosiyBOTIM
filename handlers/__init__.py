"""
handlers/__init__.py
------------------------
Barcha routerlarni bitta ro'yxatga yig'ib, dispatcher.py'ga uzatadi.

TARTIB JUDA MUHIM:
    1. admin_stats     -> /stats kabi admin komandalar (eng maxsus, eng oldin)
    2. start           -> /start komandasi
    3. subscription    -> obunani tekshirish callback
    4. registration    -> FSM: ro'yxatdan o'tish
    5. settings        -> FSM + inline: profil sozlamalari
    6. profile         -> "Mening profilim" tugmasi
    7. premium_prompt  -> paket tanlash, referal havola
    8. payment_receipt -> chek rasmini qabul qilish (FSM)
    9. admin_approval  -> admin guruhida tasdiqlash/rad etish
   10. search          -> suhbatdosh qidirish tugmalari
   11. chat_relay      -> ENG OXIRIDA: suhbatni yakunlash + qolgan barcha xabarlarni "catch-all" sifatida ushlab, relay qilish

chat_relay eng oxirida turishi SHART, chunki uning ichida `@router.message()`
(hech qanday filtrsiz) bor — bu boshqa hech bir handlerga mos kelmagan
xabarlarni "catch" qiladi. Agar u yuqorida tursa, boshqa handlerlar ishlamay qoladi.
"""

from handlers import (
    admin_approval,
    admin_stats,
    chat_relay,
    payment_receipt,
    premium_prompt,
    profile,
    registration,
    search,
    settings,
    start,
    subscription,
)

routers = [
    admin_stats.router,
    start.router,
    subscription.router,
    registration.router,
    settings.router,
    profile.router,
    premium_prompt.router,
    payment_receipt.router,
    admin_approval.router,
    search.router,
    chat_relay.router,  # DIQQAT: har doim ro'yxat oxirida bo'lishi kerak
]
