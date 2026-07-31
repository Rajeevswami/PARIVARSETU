import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PasswordResetToken

from .factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


class TestChangePassword:
    def _login(self, api_client, user, password="Str0ng!Pass1"):
        resp = api_client.post(
            reverse("accounts:login"),
            {"identifier": user.email, "password": password},
            format="json",
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")

    def test_change_password_succeeds_with_correct_old_password(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        self._login(api_client, user)

        resp = api_client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "Str0ng!Pass1",
                "new_password": "NewStr0ng!Pass2",
                "confirm_password": "NewStr0ng!Pass2",
            },
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("NewStr0ng!Pass2")

    def test_change_password_rejects_wrong_old_password(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        self._login(api_client, user)

        resp = api_client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "WrongOld1!",
                "new_password": "NewStr0ng!Pass2",
                "confirm_password": "NewStr0ng!Pass2",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_change_password_rejects_mismatched_confirmation(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        self._login(api_client, user)

        resp = api_client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "Str0ng!Pass1",
                "new_password": "NewStr0ng!Pass2",
                "confirm_password": "Different1!",
            },
            format="json",
        )
        assert resp.status_code == 400

    @pytest.mark.parametrize(
        "weak_password",
        ["short1!", "nouppercase1!", "NOLOWERCASE1!", "NoNumbers!!", "NoSpecialChar1"],
    )
    def test_change_password_rejects_weak_passwords(self, api_client, weak_password):
        user = UserFactory(password="Str0ng!Pass1")
        self._login(api_client, user)

        resp = api_client.post(
            reverse("accounts:change_password"),
            {
                "old_password": "Str0ng!Pass1",
                "new_password": weak_password,
                "confirm_password": weak_password,
            },
            format="json",
        )
        assert resp.status_code == 400


class TestForgotAndResetPassword:
    def test_forgot_password_always_returns_200(self, api_client):
        resp = api_client.post(
            reverse("accounts:forgot_password"),
            {"identifier": "nobody@parivarsetu.app"},
            format="json",
        )
        assert resp.status_code == 200

    def test_forgot_password_creates_token_for_existing_user(self, api_client):
        user = UserFactory()
        api_client.post(
            reverse("accounts:forgot_password"), {"identifier": user.email}, format="json"
        )
        assert PasswordResetToken.objects.filter(user=user).exists()

    def test_reset_password_with_valid_token(self, api_client):
        user = UserFactory(password="Str0ng!Pass1")
        token = PasswordResetToken.objects.create(
            user=user,
            token="valid-token-123",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
        )
        resp = api_client.post(
            reverse("accounts:reset_password"),
            {
                "token": token.token,
                "new_password": "BrandNew!Pass9",
                "confirm_password": "BrandNew!Pass9",
            },
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("BrandNew!Pass9")

    def test_reset_password_rejects_expired_token(self, api_client):
        user = UserFactory()
        token = PasswordResetToken.objects.create(
            user=user,
            token="expired-token",
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        resp = api_client.post(
            reverse("accounts:reset_password"),
            {
                "token": token.token,
                "new_password": "BrandNew!Pass9",
                "confirm_password": "BrandNew!Pass9",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_reset_password_rejects_already_used_token(self, api_client):
        user = UserFactory()
        token = PasswordResetToken.objects.create(
            user=user,
            token="used-token",
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
            used_at=timezone.now(),
        )
        resp = api_client.post(
            reverse("accounts:reset_password"),
            {
                "token": token.token,
                "new_password": "BrandNew!Pass9",
                "confirm_password": "BrandNew!Pass9",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_reset_password_rejects_unknown_token(self, api_client):
        resp = api_client.post(
            reverse("accounts:reset_password"),
            {
                "token": "does-not-exist",
                "new_password": "BrandNew!Pass9",
                "confirm_password": "BrandNew!Pass9",
            },
            format="json",
        )
        assert resp.status_code == 400
