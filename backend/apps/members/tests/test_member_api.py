import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
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


class TestMemberList:
    def test_family_isolation(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        MemberFactory(family=family_a, display_name="Alice")
        MemberFactory(family=family_b, display_name="Bob")
        user_a = UserFactory(password="Str0ng!Pass1", family=family_a)
        client = _authed_client(user_a)

        resp = client.get(reverse("members:member-list"))
        names = [m["display_name"] for m in resp.data["data"]]
        assert "Bob" not in names

    def test_search_by_display_name(self):
        family = FamilyFactory()
        MemberFactory(family=family, display_name="Priya Sharma")
        MemberFactory(family=family, display_name="Rahul Verma")
        user = UserFactory(password="Str0ng!Pass1", family=family)
        client = _authed_client(user)

        resp = client.get(reverse("members:member-list"), {"search": "Priya"})
        assert resp.data["meta"]["count"] == 1
        assert resp.data["data"][0]["display_name"] == "Priya Sharma"

    def test_filter_by_relationship(self):
        family = FamilyFactory()
        MemberFactory(family=family, relationship="son")
        MemberFactory(family=family, relationship="daughter")
        user = UserFactory(password="Str0ng!Pass1", family=family)
        client = _authed_client(user)

        resp = client.get(reverse("members:member-list"), {"relationship": "son"})
        assert resp.data["meta"]["count"] == 1


class TestMemberProfilePermissions:
    def test_member_can_view_own_profile(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        member = MemberFactory(family=family, user=user)
        client = _authed_client(user)

        resp = client.get(reverse("members:member-detail", args=[member.id]))
        assert resp.status_code == 200

    def test_member_can_update_own_profile(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        member = MemberFactory(family=family, user=user)
        client = _authed_client(user)

        resp = client.patch(
            reverse("members:member-detail", args=[member.id]),
            {"occupation": "Engineer"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["data"]["occupation"] == "Engineer"

    def test_member_cannot_update_another_members_profile(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family)
        MemberFactory(family=family, user=user)
        other_member = MemberFactory(family=family)
        client = _authed_client(user)

        resp = client.patch(
            reverse("members:member-detail", args=[other_member.id]),
            {"occupation": "Hacker"},
            format="json",
        )
        assert resp.status_code == 403

    def test_family_admin_can_update_other_members_profile(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        other_member = MemberFactory(family=family)
        client = _authed_client(admin)

        resp = client.patch(
            reverse("members:member-detail", args=[other_member.id]),
            {"occupation": "Updated"},
            format="json",
        )
        assert resp.status_code == 200


class TestTransferMember:
    def test_admin_can_transfer_member_to_household_in_same_family(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        MemberFactory(family=family, user=admin)
        member = MemberFactory(family=family)
        household = HouseholdFactory(family=family)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:member-transfer", args=[member.id]),
            {"household_id": str(household.id)},
            format="json",
        )
        assert resp.status_code == 200
        member.refresh_from_db()
        assert member.household_id == household.id

    def test_cannot_transfer_member_to_household_of_another_family(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        MemberFactory(family=family_a, user=admin)
        member = MemberFactory(family=family_a)
        other_household = HouseholdFactory(family=family_b)
        client = _authed_client(admin)

        resp = client.post(
            reverse("members:member-transfer", args=[member.id]),
            {"household_id": str(other_household.id)},
            format="json",
        )
        assert resp.status_code == 403

    def test_member_cannot_transfer_self(self):
        family = FamilyFactory()
        user = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        member = MemberFactory(family=family, user=user)
        household = HouseholdFactory(family=family)
        client = _authed_client(user)

        resp = client.post(
            reverse("members:member-transfer", args=[member.id]),
            {"household_id": str(household.id)},
            format="json",
        )
        assert resp.status_code == 403
