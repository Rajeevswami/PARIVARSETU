from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.ledger.models import LedgerAccount
from apps.ledger.services import journal_service, posting_service
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


def _post_sample_journal(family):
    accounts = _accounts(family)
    journal = journal_service.create_journal(
        family_id=family.id,
        transaction_type="manual_journal",
        journal_date=str(date.today()),
        lines=[
            {
                "ledger_account": accounts["1001"].id,
                "entry_type": "debit",
                "amount": Decimal("1000"),
            },
            {
                "ledger_account": accounts["4001"].id,
                "entry_type": "credit",
                "amount": Decimal("1000"),
            },
        ],
    )
    posting_service.post_journal(actor=None, journal=journal)
    return accounts


class TestTrialBalance:
    def test_trial_balance_always_balances(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        _post_sample_journal(family)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:trial_balance"))
        assert resp.status_code == 200
        assert resp.data["data"]["grand_debit"] == resp.data["data"]["grand_credit"]

    def test_trial_balance_shows_all_seeded_accounts(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:trial_balance"))
        assert len(resp.data["data"]["rows"]) == 13


class TestAccountStatement:
    def test_statement_shows_posted_entries(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        accounts = _post_sample_journal(family)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:account_statement", args=[accounts["1001"].id]))
        assert resp.status_code == 200
        assert len(resp.data["data"]["entries"]) == 1
        assert resp.data["data"]["entries"][0]["debit"] == "1000.00"


class TestCashBook:
    def test_cash_book_reflects_cash_account(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        _post_sample_journal(family)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:cash_book"))
        assert resp.status_code == 200
        assert resp.data["data"]["account_code"] == "1001"
        assert len(resp.data["data"]["entries"]) == 1


class TestFamilySummary:
    def test_summary_reflects_income_and_cash(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        _post_sample_journal(family)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:family_summary"))
        assert resp.status_code == 200
        assert resp.data["data"]["cash_and_bank"]["Cash"] == "1000.00"
        assert resp.data["data"]["income_expense"]["income"] == "1000.00"


class TestJournalRegisterExport:
    def test_export_returns_csv(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        _post_sample_journal(family)
        client = _authed_client(admin)

        resp = client.get(reverse("ledger:journal_register_export"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert b"Journal Number" in resp.content
