import pytest

from apps.accounts.models import User, UserStatus

from .factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_create_user_hashes_password_with_argon2(self):
        user = User.objects.create_user(email="a@b.com", password="Str0ng!Pass1", first_name="A")
        assert user.password.startswith("argon2$")
        assert user.check_password("Str0ng!Pass1")

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_full_name(self):
        user = UserFactory(first_name="Ravi", last_name="Kumar")
        assert user.get_full_name() == "Ravi Kumar"

    def test_soft_delete_deactivates_and_flags_user(self):
        user = UserFactory()
        admin = UserFactory()
        user.soft_delete(deleted_by=admin)

        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.is_active is False
        assert user.status == UserStatus.INACTIVE
        assert user.deleted_by_id == admin.id
        assert user.deleted_at is not None

    def test_is_login_allowed_true_for_active_user(self):
        user = UserFactory(status=UserStatus.ACTIVE, is_active=True)
        assert user.is_login_allowed is True

    def test_is_login_allowed_false_for_blocked_user(self):
        user = UserFactory(status=UserStatus.BLOCKED)
        assert user.is_login_allowed is False

    def test_is_login_allowed_false_for_deleted_user(self):
        user = UserFactory(is_deleted=True)
        assert user.is_login_allowed is False

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(email="root@parivarsetu.app", password="Str0ng!Pass1")
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.is_verified is True
