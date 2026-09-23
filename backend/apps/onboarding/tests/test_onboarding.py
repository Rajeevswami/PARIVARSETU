import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory

pytestmark = pytest.mark.django_db


def test_family_step_is_complete_when_the_user_has_a_family():
    user = UserFactory(family=FamilyFactory(), password="Str0ng!Pass1")
    client = APIClient()
    login = client.post(
        reverse("accounts:login"),
        {"identifier": user.email, "password": "Str0ng!Pass1"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['tokens']['access']}")
    response = client.get(reverse("onboarding:progress"))
    assert response.data["data"]["steps"]["family"] is True
    assert response.data["data"]["next"] == "household"
