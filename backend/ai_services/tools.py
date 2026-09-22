"""Family-scoped tools. Every query filters by family_id."""

from decimal import Decimal

from apps.expenses.models import Expense

from .analytics import anomalies, forecast_next_month, monthly_totals, savings_gap, suggest_category

TOOL_DEFINITIONS = [
    {
        "name": "ledger_summary",
        "description": "Monthly expense totals for the signed-in family.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "forecast_expenses",
        "description": "Forecast next month's expenses from recent history.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "detect_anomalies",
        "description": "Find expenses much larger than the family average.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "categorize_expense",
        "description": "Suggest a category for an expense title.",
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        },
    },
    {
        "name": "dispute_summary",
        "description": "Summarise unsettled expense shares that may need a family discussion.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "savings_goal",
        "description": "Compare income, expenses, and a savings goal.",
        "input_schema": {
            "type": "object",
            "properties": {"goal": {"type": "number"}, "income": {"type": "number"}},
            "required": ["goal", "income"],
        },
    },
    {
        "name": "extract_receipt",
        "description": "Turn receipt text or an OCR note into amount, title, and date.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]


def run_tool(name: str, arguments: dict, *, family_id) -> dict:
    expenses = list(
        Expense.objects.filter(family_id=family_id, is_deleted=False).order_by("expense_date")[:500]
    )
    if name == "ledger_summary":
        return {"months": monthly_totals(expenses)}
    if name == "forecast_expenses":
        return forecast_next_month(expenses)
    if name == "detect_anomalies":
        return {"anomalies": anomalies(expenses)}
    if name == "categorize_expense":
        from apps.expenses.models import ExpenseCategory

        names = list(
            ExpenseCategory.objects.filter(family_id=family_id, is_deleted=False).values_list(
                "name", flat=True
            )
        )
        return {"category": suggest_category(arguments.get("title", ""), names)}
    if name == "dispute_summary":
        pending = [
            {"title": expense.title, "amount": str(expense.amount), "status": expense.status}
            for expense in expenses
            if expense.status in {"pending", "approved"}
        ][:20]
        return {
            "open_items": pending,
            "note": "These are unsettled family records, not a legal finding.",
        }
    if name == "savings_goal":
        spent = sum((expense.amount for expense in expenses), Decimal("0"))
        return savings_gap(
            income=Decimal(str(arguments.get("income", 0))),
            expenses=spent,
            goal=Decimal(str(arguments.get("goal", 0))),
        )
    if name == "extract_receipt":
        return _extract_receipt(arguments.get("text", ""))
    return {"error": "unknown_tool"}


def _extract_receipt(text: str) -> dict:
    amount = ""
    for token in text.replace(",", " ").split():
        cleaned = token.strip("₹$")
        try:
            amount = f"{Decimal(cleaned):.2f}"
            break
        except Exception:
            continue
    return {
        "title": text.split("\n")[0][:80] or "Receipt",
        "amount": amount or "0.00",
        "raw": text[:500],
    }
