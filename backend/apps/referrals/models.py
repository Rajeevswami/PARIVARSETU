import uuid

from django.conf import settings
from django.db import models


class ReferralCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_code"
    )
    code = models.CharField(max_length=16, unique=True)
    max_uses = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referrals_code"


class ReferralRedemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE, related_name="redemptions")
    redeemed_by = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_redemption"
    )
    family = models.ForeignKey(
        "families.Family",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referral_redemptions",
    )
    credit_days = models.PositiveIntegerField(default=14)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referrals_redemption"
