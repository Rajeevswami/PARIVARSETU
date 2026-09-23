import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    response = client.post(
        reverse("accounts:login"),
        {"identifier": user.email, "password": "Str0ng!Pass1"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return client


class TestPrivacy:
    def test_terms_are_public(self):
        response = APIClient().get(reverse("privacy:legal", args=["terms"]))
        assert response.status_code == 200
        assert "India" in response.data["data"]["body"]

    def test_export_contains_only_the_caller(self):
        family = FamilyFactory()
        user = UserFactory(family=family, first_name="Asha")
        other = UserFactory(family=family, first_name="Other")
        response = _client(user).post(reverse("privacy:export"))
        assert response.status_code == 200
        assert response.data["data"]["user"]["first_name"] == "Asha"
        assert other.email not in response.content.decode()

    def test_deletion_anonymises_the_login(self):
        user = UserFactory()
        original = user.email
        response = _client(user).post(reverse("privacy:deletion"), {"confirm": True}, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email != original
        assert user.is_active is False

    def test_consent_can_be_anonymous(self):
        response = APIClient().post(
            reverse("privacy:consent"), {"analytics": False, "marketing": False}, format="json"
        )
        assert response.status_code == 201
