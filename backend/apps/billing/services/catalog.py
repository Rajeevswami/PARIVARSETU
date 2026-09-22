"""Plan catalog. Limits live here so views never hard-code prices or quotas."""

from apps.billing.models import Plan, PlanCode

CATALOG = (
    {
        "code": PlanCode.FREE,
        "name": "Free",
        "price_inr_paise": 0,
        "price_usd_cents": 0,
        "member_limit": 3,
        "household_limit": 1,
        "monthly_expense_limit": 50,
        "storage_mb": 50,
        "ai_enabled": False,
    },
    {
        "code": PlanCode.FAMILY,
        "name": "Family",
        "price_inr_paise": 49900,
        "price_usd_cents": 999,
        "member_limit": 15,
        "household_limit": 5,
        "monthly_expense_limit": 2000,
        "storage_mb": 2048,
        "ai_enabled": False,
    },
    {
        "code": PlanCode.PREMIUM,
        "name": "Premium",
        "price_inr_paise": 149900,
        "price_usd_cents": 2499,
        "member_limit": None,
        "household_limit": None,
        "monthly_expense_limit": None,
        "storage_mb": 20480,
        "ai_enabled": True,
    },
)

# Family.subscription_plan still uses the original choice set.
FAMILY_PLAN_FIELD = {
    PlanCode.FREE: "free",
    PlanCode.FAMILY: "basic",
    PlanCode.PREMIUM: "premium",
}


def ensure_catalog() -> None:
    for spec in CATALOG:
        Plan.objects.update_or_create(code=spec["code"], defaults=spec)
