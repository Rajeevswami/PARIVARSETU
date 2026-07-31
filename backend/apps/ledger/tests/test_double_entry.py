"""
DB-backed double-entry tests: journal creation validation, posting,
balance updates, immutability, and financial-period enforcement.
"""

from decimal import Decimal

import pytest

from apps.common.exceptions import ApplicationError
from apps.families.tests.factories import FamilyFactory
from apps.ledger.models import AccountBalance, FinancialPeriod, JournalStatus, LedgerAccount
from apps.ledger.services import journal_service, posting_service

pytestmark = pytest.mark.django_db


def _accounts(family):
    return {a.account_code: a for a in LedgerAccount.objects.filter(family=family)}


class TestJournalCreationValidation:
    def test_balanced_journal_is_created_as_draft(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-01-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("100"),
                },
                {
                    "ledger_account": accounts["1002"].id,
                    "entry_type": "credit",
                    "amount": Decimal("100"),
                },
            ],
        )
        assert journal.status == JournalStatus.DRAFT

    def test_unbalanced_journal_rejected(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        with pytest.raises(ApplicationError) as exc_info:
            journal_service.create_journal(
                family_id=family.id,
                transaction_type="manual_journal",
                journal_date="2026-01-01",
                lines=[
                    {
                        "ledger_account": accounts["1001"].id,
                        "entry_type": "debit",
                        "amount": Decimal("100"),
                    },
                    {
                        "ledger_account": accounts["1002"].id,
                        "entry_type": "credit",
                        "amount": Decimal("50"),
                    },
                ],
            )
        assert exc_info.value.code == "unbalanced_journal"

    def test_empty_journal_rejected(self):
        family = FamilyFactory()
        with pytest.raises(ApplicationError) as exc_info:
            journal_service.create_journal(
                family_id=family.id,
                transaction_type="manual_journal",
                journal_date="2026-01-01",
                lines=[],
            )
        assert exc_info.value.code == "empty_journal"

    def test_cross_family_account_rejected(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        accounts_a = _accounts(family_a)
        accounts_b = _accounts(family_b)
        with pytest.raises(ApplicationError) as exc_info:
            journal_service.create_journal(
                family_id=family_a.id,
                transaction_type="manual_journal",
                journal_date="2026-01-01",
                lines=[
                    {
                        "ledger_account": accounts_a["1001"].id,
                        "entry_type": "debit",
                        "amount": Decimal("100"),
                    },
                    {
                        "ledger_account": accounts_b["1002"].id,
                        "entry_type": "credit",
                        "amount": Decimal("100"),
                    },
                ],
            )
        assert exc_info.value.code == "cross_family_account"


class TestPosting:
    def test_posting_updates_account_balances(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("300"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("300"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=journal)

        cash_balance = AccountBalance.objects.get(account=accounts["1001"])
        income_balance = AccountBalance.objects.get(account=accounts["4001"])
        assert cash_balance.current_balance == Decimal("300")  # Assets: debit increases
        assert income_balance.current_balance == Decimal("300")  # Income: credit increases

    def test_posting_marks_journal_posted(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("50"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("50"),
                },
            ],
        )
        posted = posting_service.post_journal(actor=None, journal=journal)
        assert posted.status == JournalStatus.POSTED
        assert posted.posted_at is not None

    def test_cannot_post_twice(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("50"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("50"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=journal)
        with pytest.raises(ApplicationError) as exc_info:
            posting_service.post_journal(actor=None, journal=journal)
        assert exc_info.value.code == "duplicate_posting"

    def test_creates_ledger_entries_with_opening_and_closing_balance(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("100"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("100"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=journal)

        cash_entry = journal.ledger_entries.get(ledger_account=accounts["1001"])
        assert cash_entry.opening_balance == Decimal("0")
        assert cash_entry.closing_balance == Decimal("100")

    def test_second_posting_uses_previous_closing_as_opening(self):
        family = FamilyFactory()
        accounts = _accounts(family)

        j1 = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("100"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("100"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=j1)

        j2 = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-02",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("50"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("50"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=j2)

        cash_entry_2 = j2.ledger_entries.get(ledger_account=accounts["1001"])
        assert cash_entry_2.opening_balance == Decimal("100")
        assert cash_entry_2.closing_balance == Decimal("150")

    def test_posting_rejected_when_period_closed(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        period = FinancialPeriod.objects.get(family=family)
        period.status = "closed"
        period.save()

        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date=period.start_date,
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("10"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("10"),
                },
            ],
        )
        with pytest.raises(ApplicationError) as exc_info:
            posting_service.post_journal(actor=None, journal=journal)
        assert exc_info.value.code == "period_closed"

    def test_liability_account_credit_increases_balance(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date="2026-06-01",
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("1000"),
                },
                {
                    "ledger_account": accounts["2001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("1000"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=journal)
        loan_balance = AccountBalance.objects.get(account=accounts["2001"])
        assert loan_balance.current_balance == Decimal("1000")
