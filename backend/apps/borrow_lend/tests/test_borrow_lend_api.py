import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.borrow_lend.tests.factories import BorrowTransactionFactory, LendTransactionFactory
from apps.families.tests.factories import FamilyFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestCreateBorrow:
    def test_create_with_external_lender(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:borrow-list"),
            {
                "borrower": str(me.id),
                "external_lender_name": "Neighbour Raj",
                "amount": "500.00",
                "date": "2026-01-01",
                "payment_method": "cash",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["transaction_number"].startswith("BRW-")

    def test_create_with_internal_lender(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        lender = MemberFactory(family=family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:borrow-list"),
            {
                "borrower": str(me.id),
                "lender": str(lender.id),
                "amount": "500.00",
                "date": "2026-01-01",
                "payment_method": "cash",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_missing_lender_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:borrow-list"),
            {
                "borrower": str(me.id),
                "amount": "500.00",
                "date": "2026-01-01",
                "payment_method": "cash",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "lender_required"

    def test_borrower_and_lender_cannot_be_same(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:borrow-list"),
            {
                "borrower": str(me.id),
                "lender": str(me.id),
                "amount": "500.00",
                "date": "2026-01-01",
                "payment_method": "cash",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "same_party"


class TestCreateLend:
    def test_create_with_external_receiver(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:lend-list"),
            {
                "giver": str(me.id),
                "external_receiver_name": "Cousin Priya",
                "amount": "300.00",
                "date": "2026-01-01",
                "payment_method": "upi",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["transaction_number"].startswith("LND-")

    def test_giver_and_receiver_cannot_be_same(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:lend-list"),
            {
                "giver": str(me.id),
                "receiver": str(me.id),
                "amount": "300.00",
                "date": "2026-01-01",
                "payment_method": "upi",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "same_party"


class TestFamilyIsolation:
    def test_borrow_list_isolated_by_family(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin_a)
        BorrowTransactionFactory(family=family_a, borrower=MemberFactory(family=family_a))
        BorrowTransactionFactory(family=family_b, borrower=MemberFactory(family=family_b))
        client = _authed_client(admin_a)

        resp = client.get(reverse("borrow_lend:borrow-list"))
        assert resp.data["meta"]["count"] == 1

    def test_lend_list_isolated_by_family(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin_a)
        LendTransactionFactory(family=family_a, giver=MemberFactory(family=family_a))
        LendTransactionFactory(family=family_b, giver=MemberFactory(family=family_b))
        client = _authed_client(admin_a)

        resp = client.get(reverse("borrow_lend:lend-list"))
        assert resp.data["meta"]["count"] == 1
