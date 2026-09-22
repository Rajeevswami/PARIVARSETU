"""Deterministic ledger helpers. Claude may call them; it does not invent the numbers."""

from collections import defaultdict
from decimal import Decimal
from statistics import mean


def monthly_totals(expenses) -> list[dict]:
    buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for expense in expenses:
        key = expense.expense_date.strftime("%Y-%m")
        buckets[key] += expense.amount
    return [{"month": month, "total": str(total)} for month, total in sorted(buckets.items())]


def forecast_next_month(expenses) -> dict:
    totals = [Decimal(row["total"]) for row in monthly_totals(expenses)]
    if not totals:
        return {"next_month": "0.00", "method": "insufficient_history"}
    recent = totals[-3:]
    return {"next_month": f"{mean(recent):.2f}", "method": "trailing_three_month_mean"}


def anomalies(expenses) -> list[dict]:
    if len(expenses) < 4:
        return []
    amounts = [expense.amount for expense in expenses]
    average = mean(amounts)
    cutoff = average * 3
    return [
        {"id": str(expense.id), "title": expense.title, "amount": str(expense.amount)}
        for expense in expenses
        if expense.amount > cutoff
    ]


def suggest_category(title: str, categories: list[str]) -> str:
    lowered = title.lower()
    for name in categories:
        if name.lower() in lowered or lowered in name.lower():
            return name
    keywords = {
        "grocer": "Groceries",
        "medical": "Medical",
        "school": "Education",
        "rent": "Household",
    }
    for needle, label in keywords.items():
        if needle in lowered and label in categories:
            return label
    return categories[0] if categories else "Uncategorised"


def savings_gap(*, income: Decimal, expenses: Decimal, goal: Decimal) -> dict:
    saved = income - expenses
    remaining = max(goal - saved, Decimal("0"))
    return {"saved": f"{saved:.2f}", "remaining": f"{remaining:.2f}", "on_track": saved >= goal}
