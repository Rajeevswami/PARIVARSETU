import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.expenses.models import ExpenseParticipant, ExpenseStatus, LedgerPostingQueue
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


def _create_expense_with_participant(client, me, amount="500.00"):
    resp = client.post(
        reverse("expenses:expense-list"),
        {
            "title": "Test expense",
            "expense_date": "2026-07-01",
            "amount": amount,
            "paid_by": str(me.id),
            "payment_method": "cash",
            "visibility": "family",
            "split_type": "equal",
            "participants": [{"member_id": str(me.id)}],
        },
        format="json",
    )
    return resp.data["data"]["id"]


class TestSettlement:
    def test_partial_then_full_settlement_updates_participant_status(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "500.00")

        client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "200.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        participant = ExpenseParticipant.objects.get(expense_id=expense_id, member=me)
        assert participant.status == "partially_settled"
        assert participant.pending_amount == 300

        client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "300.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        participant.refresh_from_db()
        assert participant.status == "settled"
        assert participant.pending_amount == 0

    def test_expense_status_becomes_settled_when_all_participants_settled(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "100.00")

        client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "100.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        from apps.expenses.models import Expense

        expense = Expense.objects.get(id=expense_id)
        assert expense.status == ExpenseStatus.SETTLED

    def test_overpaying_settlement_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "100.00")

        resp = client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "150.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "duplicate_or_excess_settlement"

    def test_settling_twice_up_to_exact_share_then_rejecting_a_third(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "100.00")

        client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "100.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        # Any further settlement should be rejected — already fully settled.
        resp = client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "0.01", "settlement_date": "2026-07-02"},
            format="json",
        )
        assert resp.status_code == 400

    def test_zero_amount_settlement_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "100.00")

        resp = client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "0", "settlement_date": "2026-07-02"},
            format="json",
        )
        assert resp.status_code == 400


class TestLedgerPostingQueue:
    def test_create_expense_queues_a_ledger_posting(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "250.00")

        postings = LedgerPostingQueue.objects.filter(expense_id=expense_id)
        assert postings.filter(event_type="expense_created").exists()

    def test_settlement_queues_a_ledger_posting(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "250.00")

        client.post(
            reverse("expenses:expense-settle", args=[expense_id]),
            {"member_id": str(me.id), "paid_amount": "250.00", "settlement_date": "2026-07-02"},
            format="json",
        )
        assert LedgerPostingQueue.objects.filter(
            expense_id=expense_id, event_type="settlement_recorded"
        ).exists()

    def test_cancel_expense_queues_a_ledger_posting(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)
        expense_id = _create_expense_with_participant(client, me, "100.00")

        client.delete(reverse("expenses:expense-detail", args=[expense_id]))
        assert LedgerPostingQueue.objects.filter(
            expense_id=expense_id, event_type="expense_cancelled"
        ).exists()


class TestExpenseCategory:
    def test_family_admin_can_create_category(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-category-list"),
            {"name": "Pets", "color": "#123456"},
            format="json",
        )
        assert resp.status_code == 201

    def test_member_cannot_create_category(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        MemberFactory(family=family, user=member)
        client = _authed_client(member)

        resp = client.post(
            reverse("expenses:expense-category-list"), {"name": "Pets"}, format="json"
        )
        assert resp.status_code == 403

    def test_duplicate_category_name_in_family_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        client.post(reverse("expenses:expense-category-list"), {"name": "Pets"}, format="json")
        resp = client.post(
            reverse("expenses:expense-category-list"), {"name": "Pets"}, format="json"
        )
        assert resp.status_code == 400
