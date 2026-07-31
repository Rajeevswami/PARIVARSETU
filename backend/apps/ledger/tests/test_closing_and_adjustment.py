from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.common.exceptions import ApplicationError
from apps.families.tests.factories import FamilyFactory
from apps.ledger.models import FinancialPeriod, JournalStatus, LedgerAccount, OpeningBalance
from apps.ledger.services import closing_service, journal_service, posting_service
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


def _accounts(family):
    return {a.account_code: a for a in LedgerAccount.objects.filter(family=family)}


class TestClosingPeriod:
    def test_close_period_with_no_draft_journals_succeeds(self):
        family = FamilyFactory()
        period = FinancialPeriod.objects.get(family=family)

        closing = closing_service.close_period(actor=None, period=period)
        period.refresh_from_db()
        assert period.status == "closed"
        assert closing.financial_period_id == period.id

    def test_close_period_creates_next_period_opening_balances(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        period = FinancialPeriod.objects.get(family=family)

        journal = journal_service.create_journal(
            family_id=family.id,
            transaction_type="manual_journal",
            journal_date=period.start_date,
            lines=[
                {
                    "ledger_account": accounts["1001"].id,
                    "entry_type": "debit",
                    "amount": Decimal("500"),
                },
                {
                    "ledger_account": accounts["4001"].id,
                    "entry_type": "credit",
                    "amount": Decimal("500"),
                },
            ],
        )
        posting_service.post_journal(actor=None, journal=journal)

        closing_service.close_period(actor=None, period=period)

        next_period = FinancialPeriod.objects.exclude(id=period.id).get(family=family)
        opening = OpeningBalance.objects.get(
            ledger_account=accounts["1001"], financial_period=next_period
        )
        assert opening.amount == Decimal("500")
        assert opening.entry_type == "debit"

    def test_cannot_close_period_with_draft_journals(self):
        family = FamilyFactory()
        accounts = _accounts(family)
        period = FinancialPeriod.objects.get(family=family)

        journal_service.create_journal(
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
            closing_service.close_period(actor=None, period=period)
        assert exc_info.value.code == "draft_journals_remain"

    def test_cannot_close_already_closed_period(self):
        family = FamilyFactory()
        period = FinancialPeriod.objects.get(family=family)
        closing_service.close_period(actor=None, period=period)

        with pytest.raises(ApplicationError) as exc_info:
            closing_service.close_period(actor=None, period=period)
        assert exc_info.value.code == "already_closed"

    def test_admin_can_close_via_api(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        period = FinancialPeriod.objects.get(family=family)
        client = _authed_client(admin)

        resp = client.post(reverse("ledger:financial-period-close", args=[period.id]))
        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "closed"

    def test_member_cannot_close_period(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        period = FinancialPeriod.objects.get(family=family)
        client = _authed_client(member)

        resp = client.post(reverse("ledger:financial-period-close", args=[period.id]))
        assert resp.status_code == 403


class TestAdjustmentEntry:
    def test_admin_can_create_adjustment(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        accounts = _accounts(family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("ledger:adjustment-list"),
            {
                "journal_date": str(date.today()),
                "reason": "Correcting a miscategorized expense",
                "lines": [
                    {
                        "ledger_account": str(accounts["5001"].id),
                        "entry_type": "credit",
                        "amount": "50.00",
                    },
                    {
                        "ledger_account": str(accounts["1001"].id),
                        "entry_type": "debit",
                        "amount": "50.00",
                    },
                ],
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_adjustment_creates_a_posted_journal(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        accounts = _accounts(family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("ledger:adjustment-list"),
            {
                "journal_date": str(date.today()),
                "reason": "Fix",
                "lines": [
                    {
                        "ledger_account": str(accounts["5001"].id),
                        "entry_type": "credit",
                        "amount": "20.00",
                    },
                    {
                        "ledger_account": str(accounts["1001"].id),
                        "entry_type": "debit",
                        "amount": "20.00",
                    },
                ],
            },
            format="json",
        )
        adjustment_journal_id = resp.data["data"]["adjustment_journal"]
        from apps.ledger.models import Journal

        journal = Journal.objects.get(id=adjustment_journal_id)
        assert journal.status == JournalStatus.POSTED

    def test_member_cannot_create_adjustment(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        accounts = _accounts(family)
        client = _authed_client(member)

        resp = client.post(
            reverse("ledger:adjustment-list"),
            {
                "journal_date": str(date.today()),
                "reason": "Fix",
                "lines": [
                    {
                        "ledger_account": str(accounts["5001"].id),
                        "entry_type": "credit",
                        "amount": "20.00",
                    },
                    {
                        "ledger_account": str(accounts["1001"].id),
                        "entry_type": "debit",
                        "amount": "20.00",
                    },
                ],
            },
            format="json",
        )
        assert resp.status_code == 403
