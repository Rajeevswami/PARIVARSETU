from datetime import date

"""Integration tests: the whole point of this module — expense/loan events actually
become posted, balanced journals without touching apps.expenses/apps.loans code."""

from decimal import Decimal

import pytest

from apps.expenses.models import LedgerPostingQueue as ExpenseQueue
from apps.expenses.models import LedgerPostingStatus as ExpenseQueueStatus
from apps.expenses.tests.factories import ExpenseFactory
from apps.families.tests.factories import FamilyFactory
from apps.ledger.models import Journal, JournalStatus
from apps.ledger.services.queue_consumer import process_pending_postings
from apps.loans.models import LedgerPostingQueue as LoanQueue
from apps.loans.models import LedgerPostingStatus as LoanQueueStatus
from apps.loans.tests.factories import LoanFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


class TestExpenseQueueConsumption:
    def test_expense_created_becomes_a_posted_balanced_journal(self):
        family = FamilyFactory()
        member = MemberFactory(family=family)
        expense = ExpenseFactory(
            family=family, paid_by=member, amount="750.00", payment_method="cash"
        )
        ExpenseQueue.objects.create(
            family=family, expense=expense, event_type="expense_created", amount="750.00"
        )

        result = process_pending_postings()
        assert result["processed"] >= 1

        journal = Journal.objects.get(
            family=family, reference_type="Expense", reference_id=str(expense.id)
        )
        assert journal.status == JournalStatus.POSTED
        entries = list(journal.entries.all())
        debit_total = sum((e.amount for e in entries if e.entry_type == "debit"), Decimal("0"))
        credit_total = sum((e.amount for e in entries if e.entry_type == "credit"), Decimal("0"))
        assert debit_total == credit_total == Decimal("750.00")

    def test_queue_item_marked_posted_after_processing(self):
        family = FamilyFactory()
        member = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=member, amount="100.00")
        item = ExpenseQueue.objects.create(
            family=family, expense=expense, event_type="expense_created", amount="100.00"
        )

        process_pending_postings()
        item.refresh_from_db()
        assert item.status == ExpenseQueueStatus.POSTED

    def test_processing_is_idempotent(self):
        family = FamilyFactory()
        member = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=member, amount="100.00")
        ExpenseQueue.objects.create(
            family=family, expense=expense, event_type="expense_created", amount="100.00"
        )

        process_pending_postings()
        journal_count_after_first = Journal.objects.filter(family=family).count()

        # Second run should find nothing pending — no duplicate journals.
        process_pending_postings()
        journal_count_after_second = Journal.objects.filter(family=family).count()
        assert journal_count_after_first == journal_count_after_second


class TestLoanQueueConsumption:
    def test_loan_created_becomes_a_posted_balanced_journal(self):
        family = FamilyFactory()
        borrower = MemberFactory(family=family)
        loan = LoanFactory(
            family=family, borrower=borrower, total_amount="5000.00", loan_date=date.today()
        )
        LoanQueue.objects.create(
            family=family,
            event_type="loan_created",
            amount="5000.00",
            source_model="Loan",
            source_id=str(loan.id),
        )

        result = process_pending_postings()
        assert result["processed"] >= 1

        journal = Journal.objects.get(
            family=family, reference_type="Loan", reference_id=str(loan.id)
        )
        assert journal.status == JournalStatus.POSTED
        entries = list(journal.entries.all())
        debit_total = sum((e.amount for e in entries if e.entry_type == "debit"), Decimal("0"))
        credit_total = sum((e.amount for e in entries if e.entry_type == "credit"), Decimal("0"))
        assert debit_total == credit_total == Decimal("5000.00")

    def test_loan_queue_item_marked_posted(self):
        family = FamilyFactory()
        borrower = MemberFactory(family=family)
        loan = LoanFactory(family=family, borrower=borrower, loan_date=date.today())
        item = LoanQueue.objects.create(
            family=family,
            event_type="loan_created",
            amount="1000.00",
            source_model="Loan",
            source_id=str(loan.id),
        )

        process_pending_postings()
        item.refresh_from_db()
        assert item.status == LoanQueueStatus.POSTED

    def test_unknown_family_without_ledger_accounts_marks_failed_not_crash(self):
        """A family somehow missing its chart of accounts shouldn't crash the
        whole batch — it should be logged and skipped, leaving the row pending."""
        family = FamilyFactory()
        from apps.ledger.models import LedgerAccount

        LedgerAccount.objects.filter(family=family).delete()

        borrower = MemberFactory(family=family)
        loan = LoanFactory(family=family, borrower=borrower, loan_date=date.today())
        item = LoanQueue.objects.create(
            family=family,
            event_type="loan_created",
            amount="1000.00",
            source_model="Loan",
            source_id=str(loan.id),
        )

        result = process_pending_postings()
        assert result["failed"] >= 1
        item.refresh_from_db()
        assert item.status == LoanQueueStatus.PENDING  # left for retry, not silently dropped


class TestExpenseSettlementQueueConsumption:
    def test_settlement_recorded_becomes_a_posted_journal(self):
        family = FamilyFactory()
        member = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=member, amount="200.00")
        ExpenseQueue.objects.create(
            family=family, expense=expense, event_type="settlement_recorded", amount="80.00"
        )

        process_pending_postings()
        journal = Journal.objects.filter(
            family=family, transaction_type="expense_settlement", reference_id=str(expense.id)
        ).first()
        assert journal is not None
        assert journal.status == JournalStatus.POSTED
