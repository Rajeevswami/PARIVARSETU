"""
Household model — a sub-unit within a Family (e.g. a specific home/branch
of an extended family). `household_code` is unique per family, not
globally, since households across different families are unrelated
tenants.

`head_of_household` references "members.Member" by string — Member also
references Household, so this is an intentional circular FK, resolved
lazily by Django. See apps/members/models.py.
"""

import secrets
import uuid

from django.db import models

from apps.common.validators import validate_phone_number


class HouseholdStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


def generate_household_code() -> str:
    return f"HH-{secrets.token_hex(3).upper()}"


class Household(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="households"
    )
    household_name = models.CharField(max_length=150)
    household_code = models.CharField(
        max_length=20, default=generate_household_code, editable=False
    )
    description = models.TextField(blank=True)

    head_of_household = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="headed_households",
    )
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=17, blank=True, validators=[validate_phone_number])

    status = models.CharField(
        max_length=20, choices=HouseholdStatus.choices, default=HouseholdStatus.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="households_created",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="households_updated",
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="households_deleted",
    )

    class Meta:
        db_table = "households_household"
        verbose_name = "Household"
        verbose_name_plural = "Households"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "household_code"], name="unique_household_code_per_family"
            )
        ]
        indexes = [
            models.Index(fields=["family", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.household_name} ({self.household_code})"

    def soft_delete(self, deleted_by=None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.status = HouseholdStatus.INACTIVE
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "status", "deleted_at", "deleted_by"])
