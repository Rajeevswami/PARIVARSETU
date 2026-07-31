"""
Models for the accounts app — the custom User model and its supporting
choice classes.

NOTE on family / household: as of the Family/Household/Member module,
these are real ForeignKeys (they were placeholder UUIDFields before that
module existed — see the migration that converts them). Kept nullable:
a brand-new user has no family until they create or join one.
"""

import uuid

from django.contrib.auth.hashers import (  # noqa: F401 (documents the hasher in use)
    Argon2PasswordHasher,
)
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.validators import validate_phone_number

from .managers import UserManager


class UserRole(models.TextChoices):
    FAMILY_ADMIN = "family_admin", "Family Admin"
    MEMBER = "member", "Member"
    FUTURE_READY = "future_ready", "Future Ready"
    READ_ONLY = "read_only", "Read Only"
    AUDITOR = "auditor", "Auditor"


class UserStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLOCKED = "blocked", "Blocked"
    PENDING_VERIFICATION = "pending_verification", "Pending Verification"


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


def profile_photo_path(instance: "User", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"profile_photos/{instance.id}.{ext}"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(
        max_length=17,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        validators=[validate_phone_number],
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to=profile_photo_path, null=True, blank=True)

    # Placeholder relationships — see module note above.
    family = models.ForeignKey(
        "families.Family", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MEMBER)
    status = models.CharField(
        max_length=25, choices=UserStatus.choices, default=UserStatus.PENDING_VERIFICATION
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Audit columns — required on every business table per project convention.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="users_created"
    )
    updated_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="users_updated"
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="users_deleted"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["household"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name

    def soft_delete(self, deleted_by: "User | None" = None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.is_active = False
        self.status = UserStatus.INACTIVE
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "is_active", "status", "deleted_at", "deleted_by"])

    @property
    def is_login_allowed(self) -> bool:
        return self.is_active and not self.is_deleted and self.status == UserStatus.ACTIVE


class PasswordResetToken(models.Model):
    """Short-lived, single-use token issued for the forgot-password flow."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_password_reset_token"

    @property
    def is_valid(self) -> bool:
        from django.utils import timezone

        return self.used_at is None and self.expires_at > timezone.now()
