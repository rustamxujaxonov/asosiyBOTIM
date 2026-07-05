"""
database/requests/__init__.py
-------------------------------
Handlerlarda qulay import qilish uchun barcha funksiyalarni shu yerga chiqaramiz.
Masalan: `from database.requests import get_user, add_to_queue` kabi ishlatish mumkin.
"""

from database.requests.chat import (
    add_to_queue,
    create_chat_session,
    end_chat_session,
    find_match,
    get_active_partner_id,
    is_in_queue,
    remove_from_queue,
)
from database.requests.payments import (
    create_payment_request,
    get_payment_request,
    resolve_payment_request,
    set_admin_message_id,
)
from database.requests.users import (
    extend_premium,
    get_or_create_user,
    get_user,
    increment_invited_count,
    mark_referral_bonus_claimed,
    update_age,
    update_full_name,
    update_gender,
    update_region,
    update_registration,
)

__all__ = [
    # users
    "get_user",
    "get_or_create_user",
    "update_registration",
    "update_full_name",
    "update_age",
    "update_gender",
    "update_region",
    "extend_premium",
    "increment_invited_count",
    "mark_referral_bonus_claimed",
    # chat / queue
    "add_to_queue",
    "remove_from_queue",
    "is_in_queue",
    "find_match",
    "create_chat_session",
    "get_active_partner_id",
    "end_chat_session",
    # payments
    "create_payment_request",
    "set_admin_message_id",
    "get_payment_request",
    "resolve_payment_request",
]
