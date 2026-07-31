import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.households.models import Household
from apps.households.tests.factories import HouseholdFactory
from apps.members.models import Member

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestHouseholdCRUD:
    def test_family_admin_can_create_household(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        client = _authed_client(admin)

        resp = client.post(
            reverse("households:household-list"),
            {
                "household_name": "Main House",
                "address": "123 Road",
                "contact_number": "+919876500000",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["data"]["household_code"].startswith("HH-")

    def test_member_cannot_create_household(self):
        family = FamilyFactory()
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        client = _authed_client(member)

        resp = client.post(
            reverse("households:household-list"), {"household_name": "Sneaky"}, format="json"
        )
        assert resp.status_code == 403

    def test_household_code_unique_per_family_not_globally(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        Household.objects.create(family=family_a, household_name="A", household_code="HH-SAME")
        # Should not raise — different family, same code is fine.
        Household.objects.create(family=family_b, household_name="B", household_code="HH-SAME")
        assert Household.objects.filter(household_code="HH-SAME").count() == 2

    def test_admin_can_deactivate_household(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        household = HouseholdFactory(family=family)
        client = _authed_client(admin)

        resp = client.delete(reverse("households:household-detail", args=[household.id]))
        assert resp.status_code == 200
        household.refresh_from_db()
        assert household.is_deleted is True
        assert household.status == "inactive"

    def test_family_isolation_on_household_list(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        HouseholdFactory(family=family_a)
        HouseholdFactory(family=family_b)
        user_a = UserFactory(password="Str0ng!Pass1", family=family_a)
        client = _authed_client(user_a)

        resp = client.get(reverse("households:household-list"))
        assert resp.data["meta"]["count"] == 1


class TestChangeHead:
    def test_admin_can_change_head_to_member_of_same_household(self):
        family = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        household = HouseholdFactory(family=family)
        member_user = UserFactory(family=family, household=household)
        member = Member.objects.create(
            user=member_user, family=family, household=household, display_name="M1"
        )
        client = _authed_client(admin)

        resp = client.post(
            reverse("households:household-change-head", args=[household.id]),
            {"member_id": str(member.id)},
            format="json",
        )
        assert resp.status_code == 200
        household.refresh_from_db()
        assert household.head_of_household_id == member.id

    def test_cannot_set_head_from_another_family(self):
        family_a = FamilyFactory()
        family_b = FamilyFactory()
        admin = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        household = HouseholdFactory(family=family_a)
        other_user = UserFactory(family=family_b)
        other_member = Member.objects.create(user=other_user, family=family_b, display_name="Other")
        client = _authed_client(admin)

        resp = client.post(
            reverse("households:household-change-head", args=[household.id]),
            {"member_id": str(other_member.id)},
            format="json",
        )
        assert resp.status_code == 403
