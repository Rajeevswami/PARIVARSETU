import uuid

from django.conf import settings
from django.db import models


class PlanCode(models.TextChoices):
    FREE = "free", "Free"
    FAMILY = "family", "Family"
    PREMIUM = "premium", "Premium"


class BillingProvider(models.TextChoices):
    MANUAL = "manual", "Manual"
    STRIPE = "stripe", "Stripe"
    RAZORPAY = "razorpay", "Razorpay"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELLED = "cancelled", "Cancelled"


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, choices=PlanCode.choices, unique=True)
    name = models.CharField(max_length=40)
    price_inr_paise = models.PositiveIntegerField(default=0)
    price_usd_cents = models.PositiveIntegerField(default=0)
    member_limit = models.PositiveIntegerField(null=True, blank=True)
    household_limit = models.PositiveIntegerField(null=True, blank=True)
    monthly_expense_limit = models.PositiveIntegerField(null=True, blank=True)
    storage_mb = models.PositiveIntegerField(default=50)
    ai_enabled = models.BooleanField(default=False)
    stripe_price_id = models.CharField(max_length=80, blank=True)
    razorpay_plan_id = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = "billing_plan"
        ordering = ["price_inr_paise"]

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.OneToOneField(
        "families.Family", on_delete=models.CASCADE, related_name="billing_subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIAL
    )
    provider = models.CharField(
        max_length=20, choices=BillingProvider.choices, default=BillingProvider.MANUAL
    )
    provider_customer_id = models.CharField(max_length=80, blank=True)
    provider_subscription_id = models.CharField(max_length=80, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscription"
        indexes = [models.Index(fields=["status", "provider"])]


class CheckoutSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="checkouts"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    provider = models.CharField(max_length=20, choices=BillingProvider.choices)
    provider_session_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, default="open")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="checkouts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_checkout_session"


class PaymentEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=BillingProvider.choices)
    event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=80)
    family = models.ForeignKey(
        "families.Family",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_events",
    )
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="processed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_payment_event"
        indexes = [models.Index(fields=["provider", "event_type"])]
