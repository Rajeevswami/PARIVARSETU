"""Weekly family summary used by the Celery task. The task does not call Claude itself."""

from apps.expenses.models import Expense

from .analytics import forecast_next_month, monthly_totals


def build_weekly_summary(family) -> str:
    expenses = list(
        Expense.objects.filter(family=family, is_deleted=False).order_by("expense_date")[:200]
    )
    months = monthly_totals(expenses)
    forecast = forecast_next_month(expenses)
    latest = months[-1]["total"] if months else "0.00"
    return (
        f"{family.family_name}: latest month {latest} INR. "
        f"Next month forecast {forecast['next_month']} INR ({forecast['method']})."
    )
