import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import ReferralCode, ReferralRedemption


def get_or_create_code(user) -> ReferralCode:
    code, _created = ReferralCode.objects.get_or_create(
        owner=user, defaults={"code": secrets.token_hex(4).upper()}
    )
    return code


@transaction.atomic
def redeem(*, user, code_value: str):
    if ReferralRedemption.objects.filter(redeemed_by=user).exists():
        raise ApplicationError("This account has already used a referral.", code="already_redeemed")
    referral = (
        ReferralCode.objects.select_for_update().filter(code=code_value.strip().upper()).first()
    )
    if referral is None or referral.owner_id == user.id:
        raise ApplicationError("Referral code is invalid.", code="invalid_referral")
    if referral.redemptions.count() >= referral.max_uses:
        raise ApplicationError("This referral code has no uses left.", code="referral_exhausted")
    redemption = ReferralRedemption.objects.create(
        code=referral, redeemed_by=user, family=user.family
    )
    _extend(user.family, redemption.credit_days)
    audit_services.record(
        actor=user,
        action="referral_redeemed",
        target_model="ReferralRedemption",
        target_id=redemption.id,
        family_id=user.family_id,
        metadata={"code": referral.code, "credit_days": redemption.credit_days},
    )
    return redemption


def _extend(family, days: int) -> None:
    if family is None:
        return
    from apps.billing.models import Subscription

    subscription = Subscription.objects.filter(family=family).first()
    if subscription is None:
        return
    start = subscription.current_period_end or timezone.now()
    subscription.current_period_end = start + timedelta(days=days)
    subscription.save(update_fields=["current_period_end", "updated_at"])
