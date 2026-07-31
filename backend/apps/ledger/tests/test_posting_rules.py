"""Pure unit tests for posting rules — every generated line set must balance."""

from decimal import Decimal

from apps.ledger.services import posting_rules


def _assert_balanced(lines: list[dict]) -> None:
    debit = sum((line["amount"] for line in lines if line["entry_type"] == "debit"), Decimal("0"))
    credit = sum((line["amount"] for line in lines if line["entry_type"] == "credit"), Decimal("0"))
    assert debit == credit
    assert debit > 0


class TestExpensePostingRules:
    def test_expense_created_balances(self):
        lines = posting_rules.expense_created_lines(
            amount=Decimal("500"), payment_method="cash", title="Groceries"
        )
        _assert_balanced(lines)
        assert lines[0]["account_code"] == "5001"  # Expense
        assert lines[1]["account_code"] == "1001"  # Cash

    def test_expense_created_maps_payment_method_to_account(self):
        for method, code in [
            ("cash", "1001"),
            ("bank", "1002"),
            ("upi", "1003"),
            ("wallet", "1004"),
        ]:
            lines = posting_rules.expense_created_lines(
                amount=Decimal("100"), payment_method=method, title="X"
            )
            assert lines[1]["account_code"] == code

    def test_expense_cancelled_is_exact_reversal(self):
        created = posting_rules.expense_created_lines(
            amount=Decimal("500"), payment_method="cash", title="X"
        )
        cancelled = posting_rules.expense_cancelled_lines(
            amount=Decimal("500"), payment_method="cash", title="X"
        )
        # Same accounts, opposite entry types.
        assert created[0]["account_code"] == cancelled[1]["account_code"]
        assert created[0]["entry_type"] != cancelled[1]["entry_type"]
        _assert_balanced(cancelled)

    def test_expense_settlement_balances(self):
        lines = posting_rules.expense_settlement_lines(amount=Decimal("250"))
        _assert_balanced(lines)


class TestLoanPostingRules:
    def test_loan_created_balances(self):
        lines = posting_rules.loan_created_lines(amount=Decimal("10000"), title="Car loan")
        _assert_balanced(lines)

    def test_loan_cancelled_is_exact_reversal(self):
        created = posting_rules.loan_created_lines(amount=Decimal("10000"), title="X")
        cancelled = posting_rules.loan_cancelled_lines(amount=Decimal("10000"), title="X")
        assert created[0]["account_code"] == cancelled[1]["account_code"]
        _assert_balanced(cancelled)

    def test_loan_payment_interest_and_principal_balances(self):
        lines = posting_rules.loan_payment_lines(
            principal_paid=Decimal("300"), interest_paid=Decimal("200"), payment_method="upi"
        )
        _assert_balanced(lines)
        assert len(lines) == 3  # principal debit + interest debit + payment credit

    def test_loan_payment_principal_only_balances(self):
        lines = posting_rules.loan_payment_lines(
            principal_paid=Decimal("500"), interest_paid=Decimal("0"), payment_method="cash"
        )
        _assert_balanced(lines)
        assert len(lines) == 2

    def test_loan_payment_zero_amounts_produces_no_lines(self):
        lines = posting_rules.loan_payment_lines(
            principal_paid=Decimal("0"), interest_paid=Decimal("0"), payment_method="cash"
        )
        assert lines == []


class TestBorrowLendPostingRules:
    def test_borrow_entry_balances(self):
        lines = posting_rules.borrow_entry_lines(amount=Decimal("1000"))
        _assert_balanced(lines)

    def test_lend_entry_balances(self):
        lines = posting_rules.lend_entry_lines(amount=Decimal("1000"))
        _assert_balanced(lines)

    def test_borrow_settlement_balances(self):
        lines = posting_rules.borrow_settlement_lines(amount=Decimal("400"))
        _assert_balanced(lines)

    def test_lend_settlement_balances(self):
        lines = posting_rules.lend_settlement_lines(amount=Decimal("400"))
        _assert_balanced(lines)

    def test_borrow_and_lend_entries_use_different_accounts(self):
        borrow = posting_rules.borrow_entry_lines(amount=Decimal("100"))
        lend = posting_rules.lend_entry_lines(amount=Decimal("100"))
        borrow_codes = {line["account_code"] for line in borrow}
        lend_codes = {line["account_code"] for line in lend}
        assert borrow_codes != lend_codes
