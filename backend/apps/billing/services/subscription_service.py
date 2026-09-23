"""Subscription lifecycle. Views call this; they do not talk to Stripe or Razorpay."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.families.models import Family

from ..models import (
    BillingProvider,
    CheckoutSession,
    PaymentEvent,
    Plan,
    PlanCode,
    Subscription,
    SubscriptionStatus,
)
from .catalog import FAMILY_PLAN_FIELD, ensure_catalog
from .gateways import get_gateway

ACTIVATING = {
    "checkout.session.completed",
    "customer.subscription.updated",
    "subscription.activated",
    "subscription.charged",
}
CANCELLING = {"customer.subscription.deleted", "subscription.cancelled", "subscription.halted"}
PAST_DUE = {"invoice.payment_failed", "subscription.pending", "payment.failed"}


def attach_free(family) -> Subscription:
    ensure_catalog()
    plan = Plan.objects.get(code=PlanCode.FREE)
    subscription, _created = Subscription.objects.get_or_create(
        family=family,
        defaults={
            "plan": plan,
            "status": SubscriptionStatus.TRIAL,
            "provider": BillingProvider.MANUAL,
        },
    )
    _sync_family(subscription)
    return subscription


def list_plans():
    ensure_catalog()
    return Plan.objects.all()


def start_checkout(*, actor, family, plan_code: str, provider: str, success_url: str) -> dict:
    if actor.role != "family_admin" or actor.family_id != family.id:
        raise ApplicationError(
            "Only the family admin can change the plan.", code="not_family_admin", status_code=403
        )
    ensure_catalog()
    plan = Plan.objects.filter(code=plan_code).first()
    if plan is None:
        raise ApplicationError("Unknown plan.", code="unknown_plan")
    session = CheckoutSession.objects.create(
        family=family, plan=plan, provider=provider, created_by=actor
    )
    result = get_gateway(provider).create_checkout(session=session, success_url=success_url)
    audit_services.record(
        actor=actor,
        action="checkout_started",
        target_model="CheckoutSession",
        target_id=session.id,
        family_id=family.id,
        metadata={"plan": plan_code, "provider": provider},
    )
    return result


@transaction.atomic
def confirm_manual(*, actor, family, checkout_id: str) -> Subscription:
    session = (
        CheckoutSession.objects.select_related("plan").filter(id=checkout_id, family=family).first()
    )
    if session is None or session.provider != BillingProvider.MANUAL:
        raise ApplicationError(
            "Checkout session was not found.", code="unknown_checkout", status_code=404
        )
    session.status = "complete"
    session.save(update_fields=["status"])
    return _activate(
        family=family,
        plan=session.plan,
        provider=BillingProvider.MANUAL,
        provider_subscription_id=str(session.id),
    )


@transaction.atomic
def apply_event(event: dict) -> dict:
    event_id = event.get("event_id")
    if not event_id:
        raise ApplicationError("Webhook event id is missing.", code="invalid_event")
    if PaymentEvent.objects.filter(event_id=event_id).exists():
        return {"status": "duplicate", "event_id": event_id}
    family = (
        Family.objects.filter(id=event.get("family_id")).first() if event.get("family_id") else None
    )
    event_type = event.get("event_type", "")
    status = "processed"
    if family and event.get("plan_code") and event_type in ACTIVATING:
        plan = Plan.objects.filter(code=event["plan_code"]).first()
        if plan:
            _activate(
                family=family,
                plan=plan,
                provider=event.get("provider", BillingProvider.MANUAL),
                provider_subscription_id=event.get("provider_subscription_id", ""),
            )
    elif family and event_type in CANCELLING:
        _set_status(family, SubscriptionStatus.CANCELLED)
    elif family and event_type in PAST_DUE:
        _set_status(family, SubscriptionStatus.PAST_DUE)
        status = "failed"
    PaymentEvent.objects.create(
        provider=event.get("provider", BillingProvider.MANUAL),
        event_id=event_id,
        event_type=event_type,
        family=family,
        payload=event.get("payload") or {},
        status=status,
    )
    return {"status": status, "event_id": event_id}


def _activate(*, family, plan: Plan, provider: str, provider_subscription_id: str) -> Subscription:
    subscription, _created = Subscription.objects.get_or_create(
        family=family, defaults={"plan": plan, "provider": provider}
    )
    subscription.plan = plan
    subscription.provider = provider
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.provider_subscription_id = provider_subscription_id
    subscription.current_period_end = timezone.now() + timedelta(days=30)
    subscription.cancel_at_period_end = False
    subscription.save()
    _sync_family(subscription)
    from apps.notifications.services.dispatch import notify_family_admins

    notify_family_admins(
        family=family,
        title=f"Plan changed to {plan.name}",
        message=f"Your family is now on the {plan.name} plan.",
        notification_type="billing",
    )
    audit_services.record(
        action="subscription_changed",
        target_model="Subscription",
        target_id=subscription.id,
        family_id=family.id,
        metadata={"plan": plan.code, "provider": provider},
    )
    return subscription


def _set_status(family, status: str) -> None:
    Subscription.objects.filter(family=family).update(status=status, updated_at=timezone.now())
    family.subscription_status = "cancelled" if status == SubscriptionStatus.CANCELLED else status
    family.save(update_fields=["subscription_status", "updated_at"])


def _sync_family(subscription: Subscription) -> None:
    family = subscription.family
    family.subscription_plan = FAMILY_PLAN_FIELD[subscription.plan.code]
    family.subscription_status = (
        "trial" if subscription.status == SubscriptionStatus.TRIAL else subscription.status
    )
    family.save(update_fields=["subscription_plan", "subscription_status", "updated_at"])
