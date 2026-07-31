import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserRole, UserStatus
from apps.families.tests.factories import FamilyFactory

from .factories import UserFactory

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestFamilyAdminActions:
    def test_family_admin_can_deactivate_member_in_same_family(self):
        family = FamilyFactory()
        admin = UserFactory(role=UserRole.FAMILY_ADMIN, family=family, password="Str0ng!Pass1")
        member = UserFactory(role=UserRole.MEMBER, family=family)
        client = _authed_client(admin)

        resp = client.post(reverse("accounts:member_deactivate", args=[member.id]))
        assert resp.status_code == 200
        member.refresh_from_db()
        assert member.status == UserStatus.INACTIVE
        assert member.is_active is False

    def test_family_admin_cannot_deactivate_member_of_another_family(self):
        admin = UserFactory(
            role=UserRole.FAMILY_ADMIN, family=FamilyFactory(), password="Str0ng!Pass1"
        )
        other_family_member = UserFactory(role=UserRole.MEMBER, family=FamilyFactory())
        client = _authed_client(admin)

        resp = client.post(reverse("accounts:member_deactivate", args=[other_family_member.id]))
        assert resp.status_code == 403

    def test_regular_member_cannot_deactivate_anyone(self):
        family = FamilyFactory()
        member = UserFactory(role=UserRole.MEMBER, family=family, password="Str0ng!Pass1")
        other_member = UserFactory(role=UserRole.MEMBER, family=family)
        client = _authed_client(member)

        resp = client.post(reverse("accounts:member_deactivate", args=[other_member.id]))
        assert resp.status_code == 403

    def test_family_admin_can_reactivate_member(self):
        family = FamilyFactory()
        admin = UserFactory(role=UserRole.FAMILY_ADMIN, family=family, password="Str0ng!Pass1")
        member = UserFactory(
            role=UserRole.MEMBER, family=family, status=UserStatus.INACTIVE, is_active=False
        )
        client = _authed_client(admin)

        resp = client.post(reverse("accounts:member_reactivate", args=[member.id]))
        assert resp.status_code == 200
        member.refresh_from_db()
        assert member.status == UserStatus.ACTIVE
        assert member.is_active is True

    def test_family_admin_can_reset_member_password(self):
        family = FamilyFactory()
        admin = UserFactory(role=UserRole.FAMILY_ADMIN, family=family, password="Str0ng!Pass1")
        member = UserFactory(role=UserRole.MEMBER, family=family, password="OldPass1!")
        client = _authed_client(admin)

        resp = client.post(reverse("accounts:member_reset_password", args=[member.id]))
        assert resp.status_code == 200
        assert "temporary_password" in resp.data["data"]

        member.refresh_from_db()
        assert not member.check_password("OldPass1!")
        assert member.check_password(resp.data["data"]["temporary_password"])


class TestSelfOrFamilyAdminPermission:
    def test_member_can_view_own_profile(self):
        member = UserFactory(role=UserRole.MEMBER, password="Str0ng!Pass1")
        client = _authed_client(member)
        resp = client.get(reverse("accounts:profile"))
        assert resp.status_code == 200
