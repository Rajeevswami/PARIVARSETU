import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.households.tests.factories import HouseholdFactory
from apps.members.models import InvitationStatus, MemberInvitation
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestSendInvitation:
    def test_family_admin_can_invite_by_email(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:invitation-list"), {"email": "invitee@parivarsetu.app"}, format="json"
        )
        assert resp.status_code == 201
        assert resp.data["data"]["status"] == "pending"

    def test_member_cannot_send_invitations(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        client = _authed_client(member)

        resp = client.post(
            reverse("members:invitation-list"), {"email": "invitee@parivarsetu.app"}, format="json"
        )
        assert resp.status_code == 403

    def test_invitation_without_email_or_mobile_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        client = _authed_client(admin)

        resp = client.post(reverse("members:invitation-list"), {}, format="json")
        assert resp.status_code == 400

    def test_cannot_invite_someone_already_in_a_family(self):
        family = FamilyFactory()
        other_family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        UserFactory(email="taken@parivarsetu.app", family=other_family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:invitation-list"), {"email": "taken@parivarsetu.app"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "already_in_family"

    def test_email_only_invitation_does_not_false_positive_on_null_mobile_users(self):
        """Regression test: Q(mobile=None) used to match any user with a null
        mobile number, incorrectly blocking almost every invitation."""
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        # Plenty of users with no mobile set, unrelated to the invitee.
        UserFactory(mobile=None)
        UserFactory(mobile=None)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:invitation-list"), {"email": "brandnew@parivarsetu.app"}, format="json"
        )
        assert resp.status_code == 201

    def test_household_must_belong_to_admins_family(self):
        family = FamilyFactory()
        other_family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        other_household = HouseholdFactory(family=other_family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:invitation-list"),
            {"email": "invitee@parivarsetu.app", "household": str(other_household.id)},
            format="json",
        )
        assert resp.status_code == 403


class TestAcceptInvitation:
    def _make_invitation(self, family, admin, **kwargs):
        return MemberInvitation.objects.create(
            family=family,
            invited_by=admin,
            token="test-token-123",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            **kwargs,
        )

    def test_accept_creates_new_account_and_member(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        self._make_invitation(family, admin, email="newperson@parivarsetu.app")
        client = APIClient()

        resp = client.post(
            reverse("members:accept_invitation"),
            {"token": "test-token-123", "first_name": "Newbie", "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["data"]["display_name"] == "Newbie"

    def test_accept_rejects_expired_invitation(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        invitation = self._make_invitation(family, admin, email="expired@parivarsetu.app")
        invitation.expires_at = timezone.now() - timezone.timedelta(days=1)
        invitation.save()
        client = APIClient()

        resp = client.post(
            reverse("members:accept_invitation"),
            {"token": "test-token-123", "first_name": "X", "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 400

    def test_accept_rejects_unknown_token(self):
        client = APIClient()
        resp = client.post(
            reverse("members:accept_invitation"),
            {"token": "does-not-exist", "first_name": "X", "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 400

    def test_accept_missing_password_for_new_user_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        self._make_invitation(family, admin, email="nopass@parivarsetu.app")
        client = APIClient()

        resp = client.post(
            reverse("members:accept_invitation"), {"token": "test-token-123"}, format="json"
        )
        assert resp.status_code == 400


class TestRejectInvitation:
    def test_reject_marks_invitation_rejected(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        invitation = MemberInvitation.objects.create(
            family=family,
            invited_by=admin,
            email="reject-me@parivarsetu.app",
            token="reject-token",
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        client = APIClient()

        resp = client.post(
            reverse("members:reject_invitation"), {"token": "reject-token"}, format="json"
        )
        assert resp.status_code == 200
        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.REJECTED

    def test_reject_unknown_token_returns_400(self):
        client = APIClient()
        resp = client.post(reverse("members:reject_invitation"), {"token": "nope"}, format="json")
        assert resp.status_code == 400
