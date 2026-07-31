"""
Pure mapping from a business event (expense created, loan payment, ...)
to a balanced set of journal lines. No DB writes here — just the
accounting judgment of which accounts to debit/credit. Kept separate so
the debit==credit invariant is unit-testable without touching the DB.

Account codes referenced (seeded per-family by apps.ledger.signals):
1001 Cash, 1002 Bank, 1003 UPI, 1004 Wallet, 1005 Lend,
1006 Settlement Clearing, 2001 Loan, 2002 Borrow, 3001 Family Balance,
3002 Household Balance, 3003 Adjustment, 4001 Income, 5001 Expense.
"""

from decimal import Decimal

PAYMENT_METHOD_TO_ACCOUNT_CODE = {
    "cash": "1001",
    "bank": "1002",
    "upi": "1003",
    "wallet": "1004",
    "card": "1002",  # cards settle through a bank account
    "cheque": "1002",
}


def _line(code: str, entry_type: str, amount: Decimal, description: str = "") -> dict:
    return {
        "account_code": code,
        "entry_type": entry_type,
        "amount": amount,
        "description": description,
    }


def expense_created_lines(*, amount: Decimal, payment_method: str, title: str) -> list[dict]:
    payment_code = PAYMENT_METHOD_TO_ACCOUNT_CODE.get(payment_method, "1001")
    return [
        _line("5001", "debit", amount, f"Expense: {title}"),
        _line(payment_code, "credit", amount, f"Paid via {payment_method}"),
    ]


def expense_cancelled_lines(*, amount: Decimal, payment_method: str, title: str) -> list[dict]:
    # Exact reversal of expense_created_lines.
    payment_code = PAYMENT_METHOD_TO_ACCOUNT_CODE.get(payment_method, "1001")
    return [
        _line(payment_code, "debit", amount, f"Reversal — {title}"),
        _line("5001", "credit", amount, f"Reversal — {title}"),
    ]


def expense_settlement_lines(*, amount: Decimal) -> list[dict]:
    return [
        _line("1001", "debit", amount, "Settlement received"),
        _line("1006", "credit", amount, "Clearing settled expense share"),
    ]


def loan_created_lines(*, amount: Decimal, title: str) -> list[dict]:
    # Money comes in against a new loan liability/receivable.
    return [
        _line("1002", "debit", amount, f"Loan disbursed: {title}"),
        _line("2001", "credit", amount, f"Loan: {title}"),
    ]


def loan_cancelled_lines(*, amount: Decimal, title: str) -> list[dict]:
    return [
        _line("2001", "debit", amount, f"Reversal — {title}"),
        _line("1002", "credit", amount, f"Reversal — {title}"),
    ]


def loan_payment_lines(
    *, principal_paid: Decimal, interest_paid: Decimal, payment_method: str
) -> list[dict]:
    payment_code = PAYMENT_METHOD_TO_ACCOUNT_CODE.get(payment_method, "1001")
    lines = []
    total = Decimal("0")
    if principal_paid > 0:
        lines.append(_line("2001", "debit", principal_paid, "Loan principal payment"))
        total += principal_paid
    if interest_paid > 0:
        lines.append(_line("5001", "debit", interest_paid, "Loan interest payment"))
        total += interest_paid
    if total > 0:
        lines.append(_line(payment_code, "credit", total, "Loan payment"))
    return lines


def borrow_entry_lines(*, amount: Decimal) -> list[dict]:
    return [
        _line("1001", "debit", amount, "Amount borrowed"),
        _line("2002", "credit", amount, "Borrow liability"),
    ]


def lend_entry_lines(*, amount: Decimal) -> list[dict]:
    return [
        _line("1005", "debit", amount, "Amount lent"),
        _line("1001", "credit", amount, "Cash lent out"),
    ]


def borrow_settlement_lines(*, amount: Decimal) -> list[dict]:
    # Paying back what was borrowed.
    return [
        _line("2002", "debit", amount, "Borrow repaid"),
        _line("1001", "credit", amount, "Cash paid out"),
    ]


def lend_settlement_lines(*, amount: Decimal) -> list[dict]:
    # Receiving back what was lent.
    return [
        _line("1001", "debit", amount, "Cash received"),
        _line("1005", "credit", amount, "Lend receivable settled"),
    ]
