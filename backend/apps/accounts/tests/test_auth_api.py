import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserStatus
from apps.audit.models import AuditLog

from .factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


class TestLogin:
    def test_login_with_email_succeeds(self, api_client):
        user = UserFactory(email="a@parivarsetu.app", password="Str0ng!Pass1")
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["success"] is True
        assert "access" in resp.data["data"]["tokens"]
        assert "refresh" in resp.data["data"]["tokens"]

    def test_login_with_mobile_succeeds(self, api_client):
        user = UserFactory(mobile="+919876543210", password="Str0ng!Pass1")
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": "+919876543210", "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["data"]["user"]["id"] == str(user.id)

    def test_login_wrong_password_returns_401(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 401
        assert resp.data["success"] is False

    def test_login_records_failed_attempt(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "wrong"},
            format="json",
        )
        assert AuditLog.objects.filter(action="login_failed", actor=user).exists()

    def test_login_rejects_blocked_account(self, api_client):
        user = UserFactory(status=UserStatus.BLOCKED, password="Str0ng!Pass1")
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["errors"]["code"] == "account_inactive"

    def test_login_rejects_deleted_account(self, api_client):
        user = UserFactory(is_deleted=True, password="Str0ng!Pass1")
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "Str0ng!Pass1"},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["errors"]["code"] == "account_deleted"

    def test_login_unknown_identifier_returns_401_not_500(self, api_client):
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": "nobody@parivarsetu.app", "password": "whatever"},
            format="json",
        )
        assert resp.status_code == 401


class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        login = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": "Str0ng!Pass1"},
            format="json",
        )
        access = login.data["data"]["tokens"]["access"]
        refresh = login.data["data"]["tokens"]["refresh"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = api_client.post(reverse("accounts:logout"), {"refresh": refresh}, format="json")
        assert resp.status_code == 200

        refresh_resp = api_client.post(
            reverse("token_refresh"), {"refresh": refresh}, format="json"
        )
        assert refresh_resp.status_code == 401

    def test_logout_requires_authentication(self, api_client):
        resp = api_client.post(reverse("accounts:logout"), {"refresh": "x"}, format="json")
        assert resp.status_code == 401

    def test_logout_all_devices_blacklists_all_tokens(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        tokens = []
        for _ in range(3):
            login = api_client.post(
                reverse("accounts:login"),
                {"identifier": user.email, "password": "Str0ng!Pass1"},
                format="json",
            )
            tokens.append(login.data["data"]["tokens"])

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens[-1]['access']}")
        resp = api_client.post(reverse("accounts:logout_all"), format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["sessions_revoked"] >= 3

        for t in tokens:
            refresh_resp = api_client.post(
                reverse("token_refresh"), {"refresh": t["refresh"]}, format="json"
            )
            assert refresh_resp.status_code == 401
