from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.ledger.models import LedgerAccount
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


class TestManualJournalAPI:
    def test_admin_can_create_and_post_manual_journal(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        accounts = _accounts(family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("ledger:journal-list"),
            {
                "journal_date": str(date.today()),
                "description": "Test",
                "lines": [
                    {
                        "ledger_account": str(accounts["1001"].id),
                        "entry_type": "debit",
                        "amount": "100.00",
                    },
                    {
                        "ledger_account": str(accounts["4001"].id),
                        "entry_type": "credit",
                        "amount": "100.00",
                    },
                ],
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["status"] == "draft"
        journal_id = resp.data["data"]["id"]

        post_resp = client.post(reverse("ledger:journal-post-entry", args=[journal_id]))
        assert post_resp.status_code == 200
        assert post_resp.data["data"]["status"] == "posted"

    def test_member_cannot_create_manual_journal(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        accounts = _accounts(family)
        client = _authed_client(member)

        resp = client.post(
            reverse("ledger:journal-list"),
            {
                "journal_date": str(date.today()),
                "lines": [
                    {
                        "ledger_account": str(accounts["1001"].id),
                        "entry_type": "debit",
                        "amount": "10.00",
                    },
                    {
                        "ledger_account": str(accounts["4001"].id),
                        "entry_type": "credit",
                        "amount": "10.00",
                    },
                ],
            },
            format="json",
        )
        assert resp.status_code == 403

    def test_member_can_view_journals(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        client = _authed_client(member)

        resp = client.get(reverse("ledger:journal-list"))
        assert resp.status_code == 200

    def test_family_isolation_on_journal_list(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin_a)
        accounts_a = _accounts(family_a)
        accounts_b = _accounts(family_b)
        client = _authed_client(admin_a)

        client.post(
            reverse("ledger:journal-list"),
            {
                "journal_date": str(date.today()),
                "lines": [
                    {
                        "ledger_account": str(accounts_a["1001"].id),
                        "entry_type": "debit",
                        "amount": "10.00",
                    },
                    {
                        "ledger_account": str(accounts_a["4001"].id),
                        "entry_type": "credit",
                        "amount": "10.00",
                    },
                ],
            },
            format="json",
        )
        resp = client.get(reverse("ledger:journal-list"))
        assert resp.data["meta"]["count"] == 1
        assert str(accounts_b["1001"].family_id) != str(family_a.id)


class TestLedgerAccountAPI:
    def test_default_accounts_seeded_on_family_creation(self):
        family = FamilyFactory()
        assert LedgerAccount.objects.filter(family=family).count() == 13

    def test_admin_can_create_custom_account(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        accounts = _accounts(family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("ledger:ledger-account-list"),
            {
                "account_code": "1099",
                "account_name": "Petty Cash",
                "account_group": str(accounts["1001"].account_group_id),
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_member_cannot_create_account(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        accounts = _accounts(family)
        client = _authed_client(member)

        resp = client.post(
            reverse("ledger:ledger-account-list"),
            {
                "account_code": "1099",
                "account_name": "Petty Cash",
                "account_group": str(accounts["1001"].account_group_id),
            },
            format="json",
        )
        assert resp.status_code == 403

    def test_system_account_code_cannot_be_changed(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        cash = _accounts(family)["1001"]
        client = _authed_client(admin)

        resp = client.patch(
            reverse("ledger:ledger-account-detail", args=[cash.id]),
            {"account_code": "9999"},
            format="json",
        )
        assert resp.status_code == 403
