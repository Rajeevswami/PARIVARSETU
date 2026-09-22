"""WhatsApp and Telegram adapters. Signature checks stay here, not in views."""

import hashlib
import hmac
import re
from datetime import date
from decimal import Decimal

from django.conf import settings

from apps.common.exceptions import ApplicationError


def verify_whatsapp(payload: bytes, signature: str) -> bool:
    secret = settings.WHATSAPP_APP_SECRET
    if not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def verify_telegram(header_secret: str) -> bool:
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    return bool(secret) and hmac.compare_digest(secret, header_secret or "")


def parse_expense_command(text: str) -> dict | None:
    match = re.match(r"(?i)^(?:expense|kharcha)\s+(.+?)\s+([0-9]+(?:\.[0-9]{1,2})?)$", text.strip())
    if not match:
        return None
    return {
        "title": match.group(1).strip(),
        "amount": Decimal(match.group(2)),
        "expense_date": date.today(),
    }


def record_channel_expense(*, user, text: str):
    parsed = parse_expense_command(text)
    if parsed is None:
        raise ApplicationError(
            "Send 'expense title 120' or 'kharcha title 120'.", code="unparsed_expense"
        )
    member = getattr(user, "member_profile", None)
    if member is None:
        raise ApplicationError("Link a family member before recording expenses.", code="no_member")
    from apps.expenses.services.expense_service import create_expense

    return create_expense(
        actor=user,
        family_id=user.family_id,
        data={
            "title": parsed["title"],
            "expense_date": parsed["expense_date"],
            "amount": parsed["amount"],
            "paid_by": member,
            "visibility": "family",
        },
        split_type="equal",
        split_data=[str(member.id)],
    )
