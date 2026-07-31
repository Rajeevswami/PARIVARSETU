"""
Member — the family-domain profile every authenticated User has, one per
Family (a User belongs to exactly one Family at a time, enforced via the
OneToOne to User plus the family FK).

NOTE on gender/date_of_birth overlap with accounts.User: the spec lists
both fields on Member Profile explicitly. Rather than remove the working
fields on User (account-level identity), Member keeps its own copy — the
family-record version, which a family admin can maintain even if it
differs from what the user set on their own account (e.g. a household
head entering details for an elderly member who doesn't use the app
directly). Keeping them separate avoids one edit silently changing the
other's meaning.
"""

import secrets
import uuid

from django.db import models

from apps.common.validators import validate_phone_number


class Relationship(models.TextChoices):
    FATHER = "father", "Father"
    MOTHER = "mother", "Mother"
    SON = "son", "Son"
    DAUGHTER = "daughter", "Daughter"
    BROTHER = "brother", "Brother"
    SISTER = "sister", "Sister"
    GRANDFATHER = "grandfather", "Grandfather"
    GRANDMOTHER = "grandmother", "Grandmother"
    UNCLE = "uncle", "Uncle"
    AUNT = "aunt", "Aunt"
    COUSIN = "cousin", "Cousin"
    OTHER = "other", "Other"


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class BloodGroup(models.TextChoices):
    A_POSITIVE = "a_positive", "A+"
    A_NEGATIVE = "a_negative", "A-"
    B_POSITIVE = "b_positive", "B+"
    B_NEGATIVE = "b_negative", "B-"
    AB_POSITIVE = "ab_positive", "AB+"
    AB_NEGATIVE = "ab_negative", "AB-"
    O_POSITIVE = "o_positive", "O+"
    O_NEGATIVE = "o_negative", "O-"
    UNKNOWN = "unknown", "Unknown"


class MaritalStatus(models.TextChoices):
    SINGLE = "single", "Single"
    MARRIED = "married", "Married"
    DIVORCED = "divorced", "Divorced"
    WIDOWED = "widowed", "Widowed"


class MemberStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


def member_photo_path(instance: "Member", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"member_photos/{instance.id}.{ext}"


def generate_employee_code() -> str:
    return f"MEM-{secrets.token_hex(4).upper()}"


class Member(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="member_profile"
    )
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="members")
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )

    employee_code = models.CharField(max_length=20, default=generate_employee_code, editable=False)
    display_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=20, choices=Relationship.choices, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=15, choices=BloodGroup.choices, blank=True)
    marital_status = models.CharField(max_length=15, choices=MaritalStatus.choices, blank=True)
    occupation = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to=member_photo_path, null=True, blank=True)

    # Readiness flags only — actual Aadhaar/PAN numbers are regulated PII
    # and belong in a dedicated, encrypted KYC module, not stored here.
    aadhaar_number_ready = models.BooleanField(default=False)
    pan_number_ready = models.BooleanField(default=False)

    emergency_contact = models.CharField(
        max_length=17, blank=True, validators=[validate_phone_number]
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=MemberStatus.choices, default=MemberStatus.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members_created",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members_updated",
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members_deleted",
    )

    class Meta:
        db_table = "members_member"
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "employee_code"], name="unique_employee_code_per_family"
            )
        ]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["household"]),
            models.Index(fields=["relationship"]),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.employee_code})"

    def soft_delete(self, deleted_by=None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.status = MemberStatus.INACTIVE
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "status", "deleted_at", "deleted_by"])


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class MemberInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="invitations"
    )
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invitations",
    )
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(
        max_length=17, null=True, blank=True, validators=[validate_phone_number]
    )
    role = models.CharField(max_length=20, default="member")
    relationship = models.CharField(max_length=20, choices=Relationship.choices, blank=True)

    invited_by = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="invitations_sent"
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "members_invitation"
        verbose_name = "Member Invitation"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(mobile__isnull=False),
                name="invitation_requires_email_or_mobile",
            )
        ]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"Invite to {self.email or self.mobile} for {self.family_id}"

    @property
    def is_valid(self) -> bool:
        from django.utils import timezone

        return self.status == InvitationStatus.PENDING and self.expires_at > timezone.now()
