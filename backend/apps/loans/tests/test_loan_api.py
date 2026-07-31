import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.households.tests.factories import HouseholdFactory
from apps.loans.tests.factories import LoanFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestCreateLoan:
    def test_create_external_loan(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Car loan",
                "borrower": str(me.id),
                "loan_source": "external",
                "external_lender_name": "ABC Bank",
                "principal_amount": "10000.00",
                "interest_rate": "12.00",
                "interest_type": "simple",
                "loan_date": "2025-01-01",
                "due_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["interest_amount"] == "1200.00"
        assert resp.data["data"]["total_amount"] == "11200.00"
        assert resp.data["data"]["status"] == "active"

    def test_create_internal_loan_requires_lender(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Internal loan",
                "borrower": str(me.id),
                "loan_source": "internal",
                "principal_amount": "1000.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "lender_required"

    def test_create_internal_loan_with_valid_lender(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        lender = MemberFactory(family=family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Internal loan",
                "borrower": str(me.id),
                "loan_source": "internal",
                "lender": str(lender.id),
                "principal_amount": "1000.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_borrower_and_lender_cannot_be_same_person(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Self loan",
                "borrower": str(me.id),
                "loan_source": "internal",
                "lender": str(me.id),
                "principal_amount": "1000.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "same_party"

    def test_cross_family_lender_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        other_family_member = MemberFactory()
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Cross family",
                "borrower": str(me.id),
                "loan_source": "internal",
                "lender": str(other_family_member.id),
                "principal_amount": "1000.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 403

    def test_negative_principal_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Bad loan",
                "borrower": str(me.id),
                "loan_source": "external",
                "external_lender_name": "X",
                "principal_amount": "-10.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        assert resp.status_code == 400


class TestLoanPermissions:
    def test_family_isolation(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin_a)
        LoanFactory(family=family_a, borrower=MemberFactory(family=family_a))
        LoanFactory(family=family_b, borrower=MemberFactory(family=family_b))
        client = _authed_client(admin_a)

        resp = client.get(reverse("loans:loan-list"))
        assert resp.data["meta"]["count"] == 1

    def test_member_only_sees_own_loans(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        me = MemberFactory(family=family, user=user)
        other_member = MemberFactory(family=family)
        LoanFactory(family=family, borrower=me)
        LoanFactory(family=family, borrower=other_member)
        client = _authed_client(user)

        resp = client.get(reverse("loans:loan-list"))
        assert resp.data["meta"]["count"] == 1

    def test_member_cannot_cancel_loan(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        me = MemberFactory(family=family, user=user)
        loan = LoanFactory(family=family, borrower=me)
        client = _authed_client(user)

        resp = client.delete(reverse("loans:loan-detail", args=[loan.id]))
        assert resp.status_code == 403

    def test_admin_can_cancel_loan(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(family=family, borrower=MemberFactory(family=family))
        client = _authed_client(admin)

        resp = client.delete(reverse("loans:loan-detail", args=[loan.id]))
        assert resp.status_code == 200
        loan.refresh_from_db()
        assert loan.is_deleted is True


class TestSearchFilterSort:
    def test_search_by_title(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        borrower = MemberFactory(family=family)
        LoanFactory(family=family, borrower=borrower, title="Car loan")
        LoanFactory(family=family, borrower=borrower, title="Home renovation")
        client = _authed_client(admin)

        resp = client.get(reverse("loans:loan-list"), {"search": "Car"})
        assert resp.data["meta"]["count"] == 1

    def test_filter_by_household(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        household = HouseholdFactory(family=family)
        borrower = MemberFactory(family=family)
        LoanFactory(family=family, borrower=borrower, household=household)
        LoanFactory(family=family, borrower=borrower)
        client = _authed_client(admin)

        resp = client.get(reverse("loans:loan-list"), {"household": str(household.id)})
        assert resp.data["meta"]["count"] == 1

    def test_sort_by_amount(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        borrower = MemberFactory(family=family)
        LoanFactory(
            family=family, borrower=borrower, principal_amount="500.00", total_amount="500.00"
        )
        LoanFactory(
            family=family, borrower=borrower, principal_amount="5000.00", total_amount="5000.00"
        )
        client = _authed_client(admin)

        resp = client.get(reverse("loans:loan-list"), {"ordering": "-total_amount"})
        amounts = [float(loan["total_amount"]) for loan in resp.data["data"]]
        assert amounts == sorted(amounts, reverse=True)
