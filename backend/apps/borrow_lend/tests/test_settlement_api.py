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


class TestBorrowSettlement:
    def test_partial_settlement_updates_status(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        borrow = BorrowTransactionFactory(family=family, borrower=me, amount="1000.00")
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "400.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        assert resp.status_code == 201
        borrow.refresh_from_db()
        assert borrow.status == "partially_settled"
        assert borrow.settled_amount == 400

    def test_full_settlement_marks_settled(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        borrow = BorrowTransactionFactory(family=family, borrower=me, amount="500.00")
        client = _authed_client(admin)

        client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "500.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        borrow.refresh_from_db()
        assert borrow.status == "settled"

    def test_over_settlement_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        borrow = BorrowTransactionFactory(family=family, borrower=me, amount="500.00")
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "600.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "duplicate_or_excess_settlement"

    def test_two_partial_settlements_then_reject_a_third(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        borrow = BorrowTransactionFactory(family=family, borrower=me, amount="1000.00")
        client = _authed_client(admin)

        client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "600.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "400.00",
                "settlement_date": "2026-02-02",
            },
            format="json",
        )
        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "borrow",
                "reference_id": str(borrow.id),
                "member_id": str(me.id),
                "amount": "1.00",
                "settlement_date": "2026-02-03",
            },
            format="json",
        )
        assert resp.status_code == 400


class TestLendSettlement:
    def test_settle_lend_transaction(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        lend = LendTransactionFactory(family=family, giver=me, amount="200.00")
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "lend",
                "reference_id": str(lend.id),
                "member_id": str(me.id),
                "amount": "200.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        assert resp.status_code == 201
        lend.refresh_from_db()
        assert lend.status == "settled"

    def test_unknown_reference_id_returns_404(self):
        import uuid

        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "lend",
                "reference_id": str(uuid.uuid4()),
                "member_id": str(me.id),
                "amount": "50.00",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        assert resp.status_code == 404

    def test_zero_amount_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        lend = LendTransactionFactory(family=family, giver=me, amount="200.00")
        client = _authed_client(admin)

        resp = client.post(
            reverse("borrow_lend:settlement"),
            {
                "reference_type": "lend",
                "reference_id": str(lend.id),
                "member_id": str(me.id),
                "amount": "0",
                "settlement_date": "2026-02-01",
            },
            format="json",
        )
        assert resp.status_code == 400
