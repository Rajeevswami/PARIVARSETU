"""Quota checks. Families without a subscription stay unlimited so existing data is not locked."""

from django.utils import timezone

from apps.common.exceptions import ApplicationError

from ..models import Subscription, SubscriptionStatus

ACTIVE = (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE)


def current_subscription(family):
    if family is None:
        return None
    return (
        Subscription.objects.filter(family=family, status__in=ACTIVE).select_related("plan").first()
    )


def assert_can_add(family, resource: str) -> None:
    subscription = current_subscription(family)
    if subscription is None:
        return
    plan = subscription.plan
    limit = {
        "members": plan.member_limit,
        "households": plan.household_limit,
        "expenses": plan.monthly_expense_limit,
    }.get(resource)
    if limit is None:
        return
    used = _used(family, resource)
    if used + 1 > limit:
        raise ApplicationError(
            f"The {plan.name} plan allows {limit} {resource}. Upgrade to add more.",
            code="plan_limit_exceeded",
            status_code=402,
        )


def ai_allowed(family) -> bool:
    subscription = current_subscription(family)
    return bool(subscription and subscription.plan.ai_enabled)


def _used(family, resource: str) -> int:
    if resource == "members":
        from apps.members.models import Member

        return Member.objects.filter(family=family, is_deleted=False).count()
    if resource == "households":
        from apps.households.models import Household

        return Household.objects.filter(family=family, is_deleted=False).count()
    if resource == "expenses":
        from apps.expenses.models import Expense

        start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Expense.objects.filter(
            family=family, is_deleted=False, created_at__gte=start
        ).count()
    return 0
