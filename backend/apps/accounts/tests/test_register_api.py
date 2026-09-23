import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import EmailVerificationToken, User, UserStatus

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "name": "Asha Sharma",
    "email": "asha@familynexus.app",
    "password": "Str0ng!Pass1",
    "confirm_password": "Str0ng!Pass1",
}


def test_register_in_production_asks_the_user_to_check_email():
    response = APIClient().post(reverse("accounts:register"), PAYLOAD, format="json")
    assert response.status_code == 201
    assert response.data["success"] is True
    assert response.data["message"] == "Check your email to verify your account."
    assert response.data["data"]["verification_required"] is True
    assert "tokens" not in response.data["data"]

    user = User.objects.get(email="asha@familynexus.app")
    assert user.first_name == "Asha"
    assert user.last_name == "Sharma"
    assert user.status == UserStatus.PENDING_VERIFICATION
    assert user.is_verified is False
    assert len(mail.outbox) == 1
    assert "Verify" in mail.outbox[0].subject

    blocked = APIClient().post(
        reverse("accounts:login"),
        {"identifier": user.email, "password": "Str0ng!Pass1"},
        format="json",
    )
    assert blocked.status_code == 403


def test_verify_email_activates_the_account_and_returns_tokens():
    APIClient().post(reverse("accounts:register"), PAYLOAD, format="json")
    token = EmailVerificationToken.objects.get().token
    assert token in mail.outbox[0].body

    response = APIClient().post(reverse("accounts:verify_email"), {"token": token}, format="json")
    assert response.status_code == 200
    assert "access" in response.data["data"]["tokens"]
    user = User.objects.get(email="asha@familynexus.app")
    assert user.status == UserStatus.ACTIVE
    assert user.is_verified is True

    reused = APIClient().post(reverse("accounts:verify_email"), {"token": token}, format="json")
    assert reused.status_code == 400
    assert reused.data["errors"]["code"] == "invalid_token"


@override_settings(DEBUG=True)
def test_register_in_development_auto_verifies_and_returns_tokens():
    response = APIClient().post(reverse("accounts:register"), PAYLOAD, format="json")
    assert response.status_code == 201
    assert response.data["data"]["verification_required"] is False
    assert response.data["data"]["tokens"]["access"]
    user = User.objects.get(email="asha@familynexus.app")
    assert user.is_verified is True
    assert user.status == UserStatus.ACTIVE
    assert len(mail.outbox) == 1


def test_register_rejects_a_duplicate_email_and_a_weak_password():
    APIClient().post(reverse("accounts:register"), PAYLOAD, format="json")
    duplicate = APIClient().post(reverse("accounts:register"), PAYLOAD, format="json")
    assert duplicate.status_code == 409
    assert duplicate.data["errors"]["code"] == "email_taken"

    mismatch = APIClient().post(
        reverse("accounts:register"),
        {**PAYLOAD, "email": "other@familynexus.app", "confirm_password": "Str0ng!Pass2"},
        format="json",
    )
    assert mismatch.status_code == 400
    assert "confirm_password" in mismatch.data["errors"]
