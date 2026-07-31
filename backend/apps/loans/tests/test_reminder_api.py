import pytest
from django.urls import reverse
from django.utils import timezone
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


class TestReminders:
    def test_create_custom_reminder(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-reminder-list"),
            {
                "member": str(me.id),
                "reminder_type": "custom",
                "title": "Follow up with lender",
                "remind_at": timezone.now().isoformat(),
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["status"] == "pending"

    def test_create_due_date_reminder_linked_to_loan(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        loan = LoanFactory(family=family, borrower=me)
        client = _authed_client(admin)

        resp = client.post(
            reverse("loans:loan-reminder-list"),
            {
                "loan": str(loan.id),
                "member": str(me.id),
                "reminder_type": "due_date",
                "title": "Loan due soon",
                "remind_at": timezone.now().isoformat(),
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["loan"] == loan.id

    def test_member_only_sees_own_reminders(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        me = MemberFactory(family=family, user=user)
        other_member = MemberFactory(family=family)
        client = _authed_client(user)

        client.post(
            reverse("loans:loan-reminder-list"),
            {
                "member": str(me.id),
                "reminder_type": "custom",
                "title": "Mine",
                "remind_at": timezone.now().isoformat(),
            },
            format="json",
        )
        # An admin creates a reminder for someone else
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        admin_client = _authed_client(admin)
        admin_client.post(
            reverse("loans:loan-reminder-list"),
            {
                "member": str(other_member.id),
                "reminder_type": "custom",
                "title": "Not mine",
                "remind_at": timezone.now().isoformat(),
            },
            format="json",
        )

        resp = client.get(reverse("loans:loan-reminder-list"))
        titles = [r["title"] for r in resp.data["data"]]
        assert "Mine" in titles
        assert "Not mine" not in titles

    def test_dismiss_reminder(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        me = MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        create_resp = client.post(
            reverse("loans:loan-reminder-list"),
            {
                "member": str(me.id),
                "reminder_type": "custom",
                "title": "Dismiss me",
                "remind_at": timezone.now().isoformat(),
            },
            format="json",
        )
        reminder_id = create_resp.data["data"]["id"]

        resp = client.post(reverse("loans:loan-reminder-dismiss", args=[reminder_id]))
        assert resp.status_code == 200

        list_resp = client.get(reverse("loans:loan-reminder-list"))
        dismissed = next(r for r in list_resp.data["data"] if r["id"] == reminder_id)
        assert dismissed["status"] == "dismissed"
