import pytest
from cryptography.fernet import Fernet
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.administration.models import ApplicationConfiguration
from apps.common.crypto import decrypt_json, encrypt_json
from apps.families.tests.factories import FamilyFactory

pytestmark = pytest.mark.django_db


def test_browser_preflight_allows_the_request_id_header():
    response = APIClient().options(
        reverse("health"),
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type,x-request-id",
    )
    assert response.status_code == 200
    assert "x-request-id" in response["Access-Control-Allow-Headers"]


def test_health_is_public():
    response = APIClient().get(reverse("health"))
    assert response.status_code == 200
    assert response.data["data"]["database"] == "ok"


def test_metrics_require_staff():
    user = UserFactory(password="Str0ng!Pass1")
    client = APIClient()
    login = client.post(
        reverse("accounts:login"),
        {"identifier": user.email, "password": "Str0ng!Pass1"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['tokens']['access']}")
    assert client.get(reverse("metrics")).status_code == 403


@override_settings(FIELD_ENCRYPTION_KEY=Fernet.generate_key().decode())
def test_provider_secrets_are_encrypted_at_rest():
    family = FamilyFactory()
    config = ApplicationConfiguration.objects.create(
        family=family, email_config={"api_key": "secret-value"}
    )
    config.refresh_from_db()
    assert "secret-value" not in str(config.email_config)
    assert decrypt_json(config.email_config)["api_key"] == "secret-value"
    assert encrypt_json({}) == {}
