import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.billing.services.subscription_service import attach_free
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


def test_referral_extends_the_redeemer_period():
    owner = UserFactory()
    code = _client(owner).get(reverse("referrals:referral")).data["data"]["code"]
    family = FamilyFactory()
    redeemer = UserFactory(family=family)
    attach_free(family)
    response = _client(redeemer).post(reverse("referrals:referral"), {"code": code}, format="json")
    assert response.status_code == 200
    assert response.data["data"]["credit_days"] == 14
