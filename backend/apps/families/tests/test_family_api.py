import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.models import Family

pytestmark = pytest.mark.django_db


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


class TestCreateFamily:
    def test_user_without_family_can_create_one(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)

        resp = client.post(
            reverse("families:family-list"), {"family_name": "Verma Family"}, format="json"
        )
        assert resp.status_code == 201
        assert resp.data["data"]["family_name"] == "Verma Family"
        assert resp.data["data"]["family_code"].startswith("FAM-")

    def test_creator_becomes_family_admin(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)

        client.post(reverse("families:family-list"), {"family_name": "Verma Family"}, format="json")
        user.refresh_from_db()
        assert user.role == "family_admin"
        assert user.family_id is not None

    def test_creator_gets_a_member_profile(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)

        resp = client.post(
            reverse("families:family-list"), {"family_name": "Verma Family"}, format="json"
        )
        assert resp.data["data"]["member_count"] == 1

    def test_user_already_in_a_family_cannot_create_another(self):
        family = Family.objects.create(family_name="Existing")
        user = UserFactory(password="Str0ng!Pass1", family=family)
        client = _authed_client(user)

        resp = client.post(
            reverse("families:family-list"), {"family_name": "New Family"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.data["errors"]["code"] == "already_in_family"

    def test_blank_family_name_rejected(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)

        resp = client.post(reverse("families:family-list"), {"family_name": "   "}, format="json")
        assert resp.status_code == 400


class TestFamilyIsolation:
    def test_user_only_sees_own_family_in_list(self):
        family_a = Family.objects.create(family_name="Family A")
        family_b = Family.objects.create(family_name="Family B")
        user_a = UserFactory(password="Str0ng!Pass1", family=family_a)
        client = _authed_client(user_a)

        resp = client.get(reverse("families:family-list"))
        ids = [f["id"] for f in resp.data["data"]]
        assert str(family_a.id) in ids
        assert str(family_b.id) not in ids

    def test_user_with_no_family_gets_empty_list(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)

        resp = client.get(reverse("families:family-list"))
        assert resp.data["data"] == []

    def test_non_admin_cannot_update_family(self):
        family = Family.objects.create(family_name="Family A")
        member = UserFactory(password="Str0ng!Pass1", family=family, role="member")
        client = _authed_client(member)

        resp = client.patch(
            reverse("families:family-detail", args=[family.id]),
            {"family_name": "Hacked"},
            format="json",
        )
        assert resp.status_code == 403

    def test_admin_can_update_own_family(self):
        family = Family.objects.create(family_name="Family A")
        admin = UserFactory(password="Str0ng!Pass1", family=family, role="family_admin")
        client = _authed_client(admin)

        resp = client.patch(
            reverse("families:family-detail", args=[family.id]), {"city": "Mumbai"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["data"]["city"] == "Mumbai"

    def test_admin_cannot_update_another_family(self):
        family_a = Family.objects.create(family_name="Family A")
        family_b = Family.objects.create(family_name="Family B")
        admin_a = UserFactory(password="Str0ng!Pass1", family=family_a, role="family_admin")
        client = _authed_client(admin_a)

        resp = client.patch(
            reverse("families:family-detail", args=[family_b.id]), {"city": "Mumbai"}, format="json"
        )
        assert resp.status_code in (403, 404)
