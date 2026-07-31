import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.expenses.models import ExpenseStatus
from apps.expenses.tests.factories import ExpenseFactory
from apps.families.tests.factories import FamilyFactory
from apps.households.tests.factories import HouseholdFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestDefaultCategorySeeding:
    def test_family_creation_seeds_default_categories(self):
        family = FamilyFactory()
        names = set(family.expense_categories.values_list("name", flat=True))
        assert {"Personal", "Household", "Medical", "Food", "Other"} <= names
        assert family.expense_categories.count() == 12


class TestCreateExpense:
    def test_equal_split_expense_created_with_participants(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        other = MemberFactory(family=family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-list"),
            {
                "title": "Dinner",
                "expense_date": "2026-07-01",
                "amount": "500.00",
                "paid_by": str(me.id),
                "payment_method": "cash",
                "visibility": "family",
                "split_type": "equal",
                "participants": [{"member_id": str(me.id)}, {"member_id": str(other.id)}],
            },
            format="json",
        )
        assert resp.status_code == 201
        shares = {str(p["member"]): p["share_amount"] for p in resp.data["data"]["participants"]}
        assert shares[str(me.id)] == "250.00"
        assert shares[str(other.id)] == "250.00"

    def test_percentage_split_must_sum_to_100(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-list"),
            {
                "title": "Bad split",
                "expense_date": "2026-07-01",
                "amount": "500.00",
                "paid_by": str(me.id),
                "payment_method": "cash",
                "split_type": "percentage",
                "participants": [{"member_id": str(me.id), "value": "60"}],
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "invalid_percentage_split"

    def test_paid_by_must_belong_to_same_family(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        other_family_member = MemberFactory()
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-list"),
            {
                "title": "Cross family",
                "expense_date": "2026-07-01",
                "amount": "100.00",
                "paid_by": str(other_family_member.id),
                "payment_method": "cash",
                "split_type": "equal",
                "participants": [{"member_id": str(other_family_member.id)}],
            },
            format="json",
        )
        assert resp.status_code == 403

    def test_blank_title_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-list"),
            {
                "title": "   ",
                "expense_date": "2026-07-01",
                "amount": "100.00",
                "paid_by": str(me.id),
                "payment_method": "cash",
                "split_type": "equal",
                "participants": [{"member_id": str(me.id)}],
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_negative_amount_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("expenses:expense-list"),
            {
                "title": "Negative",
                "expense_date": "2026-07-01",
                "amount": "-10.00",
                "paid_by": str(me.id),
                "payment_method": "cash",
                "split_type": "equal",
                "participants": [{"member_id": str(me.id)}],
            },
            format="json",
        )
        assert resp.status_code == 400


class TestExpenseVisibility:
    def test_private_expense_only_visible_to_payer_and_admin(self):
        family = FamilyFactory()
        payer_user = UserFactory(password="Str0ng!Pass1", family=family)
        payer = MemberFactory(family=family, user=payer_user)
        other_user = UserFactory(password="Str0ng!Pass1", family=family)
        MemberFactory(family=family, user=other_user)
        expense = ExpenseFactory(family=family, paid_by=payer, visibility="private")

        other_client = _authed_client(other_user)
        resp = other_client.get(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 403

        payer_client = _authed_client(payer_user)
        resp = payer_client.get(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 200

    def test_family_visible_expense_seen_by_all_members(self):
        family = FamilyFactory()
        payer_user = UserFactory(password="Str0ng!Pass1", family=family)
        payer = MemberFactory(family=family, user=payer_user)
        other_user = UserFactory(password="Str0ng!Pass1", family=family)
        MemberFactory(family=family, user=other_user)
        expense = ExpenseFactory(family=family, paid_by=payer, visibility="family")

        other_client = _authed_client(other_user)
        resp = other_client.get(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 200

    def test_household_visible_expense_only_seen_by_household_members(self):
        family = FamilyFactory()
        household = HouseholdFactory(family=family)
        payer_user = UserFactory(password="Str0ng!Pass1", family=family, household=household)
        payer = MemberFactory(family=family, user=payer_user, household=household)
        outside_user = UserFactory(password="Str0ng!Pass1", family=family)
        MemberFactory(family=family, user=outside_user)
        expense = ExpenseFactory(
            family=family, household=household, paid_by=payer, visibility="household"
        )

        outside_client = _authed_client(outside_user)
        resp = outside_client.get(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 403

    def test_admin_sees_everything_regardless_of_visibility(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=payer, visibility="private")

        client = _authed_client(admin)
        resp = client.get(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 200


class TestExpensePermissions:
    def test_member_can_edit_own_expense(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        member = MemberFactory(family=family, user=user)
        expense = ExpenseFactory(family=family, paid_by=member, visibility="family")
        client = _authed_client(user)

        resp = client.patch(
            reverse("expenses:expense-detail", args=[expense.id]),
            {"title": "Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_member_cannot_edit_others_expense(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        MemberFactory(family=family, user=user)
        other_payer = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=other_payer, visibility="family")
        client = _authed_client(user)

        resp = client.patch(
            reverse("expenses:expense-detail", args=[expense.id]),
            {"title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 403

    def test_member_cannot_cancel_any_expense(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        member = MemberFactory(family=family, user=user)
        expense = ExpenseFactory(family=family, paid_by=member, visibility="family")
        client = _authed_client(user)

        resp = client.delete(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 403

    def test_family_admin_can_cancel_expense(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        expense = ExpenseFactory(family=family, paid_by=payer, visibility="family")
        client = _authed_client(admin)

        resp = client.delete(reverse("expenses:expense-detail", args=[expense.id]))
        assert resp.status_code == 200
        expense.refresh_from_db()
        assert expense.is_deleted is True
        assert expense.status == ExpenseStatus.CANCELLED

    def test_family_isolation_on_expense_list(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin_a)
        member_b = MemberFactory(family=family_b)
        ExpenseFactory(family=family_a, paid_by=MemberFactory(family=family_a), visibility="family")
        ExpenseFactory(family=family_b, paid_by=member_b, visibility="family")

        client = _authed_client(admin_a)
        resp = client.get(reverse("expenses:expense-list"))
        assert resp.data["meta"]["count"] == 1


class TestSearchFilterSort:
    def test_search_by_title(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        ExpenseFactory(family=family, paid_by=payer, title="Grocery run", visibility="family")
        ExpenseFactory(family=family, paid_by=payer, title="Movie night", visibility="family")
        client = _authed_client(admin)

        resp = client.get(reverse("expenses:expense-list"), {"search": "Grocery"})
        assert resp.data["meta"]["count"] == 1

    def test_filter_by_status(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        ExpenseFactory(family=family, paid_by=payer, visibility="family", status="pending")
        ExpenseFactory(family=family, paid_by=payer, visibility="family", status="settled")
        client = _authed_client(admin)

        resp = client.get(reverse("expenses:expense-list"), {"status": "settled"})
        assert resp.data["meta"]["count"] == 1

    def test_date_range_filter(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        ExpenseFactory(family=family, paid_by=payer, visibility="family", expense_date="2026-01-01")
        ExpenseFactory(family=family, paid_by=payer, visibility="family", expense_date="2026-06-01")
        client = _authed_client(admin)

        resp = client.get(
            reverse("expenses:expense-list"), {"date_from": "2026-05-01", "date_to": "2026-12-31"}
        )
        assert resp.data["meta"]["count"] == 1

    def test_sort_by_amount(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        payer = MemberFactory(family=family)
        ExpenseFactory(family=family, paid_by=payer, visibility="family", amount="50.00")
        ExpenseFactory(family=family, paid_by=payer, visibility="family", amount="500.00")
        client = _authed_client(admin)

        resp = client.get(reverse("expenses:expense-list"), {"ordering": "-amount"})
        amounts = [float(e["amount"]) for e in resp.data["data"]]
        assert amounts == sorted(amounts, reverse=True)
