import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
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


class TestLoanPayments:
    def test_payment_splits_interest_first(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            principal_amount="1000.00",
            interest_amount="200.00",
            total_amount="1200.00",
            remaining_amount="1200.00",
        )
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "150.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["interest_paid"] == "150.00"
        assert resp.data["data"]["principal_paid"] == "0.00"

    def test_payment_covers_interest_then_principal(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            principal_amount="1000.00",
            interest_amount="200.00",
            total_amount="1200.00",
            remaining_amount="1200.00",
        )
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "500.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert resp.data["data"]["interest_paid"] == "200.00"
        assert resp.data["data"]["principal_paid"] == "300.00"

    def test_full_payment_completes_loan(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            total_amount="500.00",
            remaining_amount="500.00",
        )
        client = _authed_client(admin)

        client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "500.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        loan.refresh_from_db()
        assert loan.status == "completed"
        assert loan.remaining_amount == 0

    def test_overpayment_rejected_by_default(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            total_amount="500.00",
            remaining_amount="500.00",
        )
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "600.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "excess_payment"

    def test_overpayment_allowed_when_configured(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            total_amount="500.00",
            remaining_amount="500.00",
            allow_overpayment=True,
        )
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "600.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert resp.status_code == 201

    def test_zero_amount_payment_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(family=family, borrower=MemberFactory(family=family))
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "0", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert resp.status_code == 400

    def test_json_content_type_accepted_without_attachment(self):
        """Regression test: the payments endpoint used to reject any
        non-multipart request, breaking normal JSON payment submission."""
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(family=family, borrower=MemberFactory(family=family))
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "100.00", "payment_date": "2026-02-01", "payment_method": "upi"},
            format="json",
        )
        assert resp.status_code == 201


class TestLoanStatsAndExport:
    def test_stats_returns_grand_total(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        LoanFactory(family=family, borrower=MemberFactory(family=family), total_amount="1000.00")
        LoanFactory(family=family, borrower=MemberFactory(family=family), total_amount="2000.00")
        client = _authed_client(admin)

        resp = client.get(reverse("loans:loan-stats"))
        assert resp.status_code == 200
        assert float(resp.data["data"]["grand_total"]) == 3000.0

    def test_export_returns_csv(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        LoanFactory(family=family, borrower=MemberFactory(family=family))
        client = _authed_client(admin)

        resp = client.get(reverse("loans:loan-export"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert b"Loan Number" in resp.content


class TestLedgerPostingQueue:
    def test_loan_creation_queues_posting(self):
        from apps.loans.models import LedgerPostingQueue

        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-list"),
            {
                "title": "Ledger test loan",
                "borrower": str(me.id),
                "loan_source": "external",
                "external_lender_name": "X",
                "principal_amount": "100.00",
                "loan_date": "2026-01-01",
            },
            format="json",
        )
        loan_id = resp.data["data"]["id"]
        assert LedgerPostingQueue.objects.filter(
            source_id=loan_id, event_type="loan_created"
        ).exists()

    def test_payment_queues_posting(self):
        from apps.loans.models import LedgerPostingQueue

        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        loan = LoanFactory(
            family=family,
            borrower=MemberFactory(family=family),
            total_amount="500",
            remaining_amount="500",
        )
        client = _authed_client(admin)

        client.post(
            reverse("loans:loan-payments", args=[loan.id]),
            {"amount": "100.00", "payment_date": "2026-02-01", "payment_method": "cash"},
            format="json",
        )
        assert LedgerPostingQueue.objects.filter(
            event_type="loan_payment_recorded", metadata__loan_id=str(loan.id)
        ).exists()
