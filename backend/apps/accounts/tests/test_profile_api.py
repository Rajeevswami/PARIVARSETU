import io

import pytest
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from .factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def _authed_client(user, password="Str0ng!Pass1"):
    client = APIClient()
    resp = client.post(
        reverse("accounts:login"), {"identifier": user.email, "password": password}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['data']['tokens']['access']}")
    return client


def _tiny_png():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(buf, format="PNG")
    buf.seek(0)
    buf.name = "avatar.png"
    return buf


class TestProfile:
    def test_get_own_profile(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)
        resp = client.get(reverse("accounts:profile"))
        assert resp.status_code == 200
        assert resp.data["data"]["email"] == user.email

    def test_update_profile_changes_allowed_fields(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)
        resp = client.patch(reverse("accounts:profile"), {"first_name": "Updated"}, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["first_name"] == "Updated"

    def test_update_profile_cannot_change_email(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)
        original_email = user.email
        client.patch(
            reverse("accounts:profile"), {"email": "hacked@parivarsetu.app"}, format="json"
        )
        user.refresh_from_db()
        assert user.email == original_email

    def test_upload_avatar(self):
        user = UserFactory(password="Str0ng!Pass1")
        client = _authed_client(user)
        resp = client.post(
            reverse("accounts:profile_avatar"), {"profile_photo": _tiny_png()}, format="multipart"
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.profile_photo.name

    def test_profile_requires_authentication(self, api_client):
        resp = api_client.get(reverse("accounts:profile"))
        assert resp.status_code == 401
