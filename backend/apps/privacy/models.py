import uuid

from django.conf import settings
from django.db import models


class CookieConsent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cookie_consents",
    )
    anonymous_id = models.CharField(max_length=64, blank=True)
    necessary = models.BooleanField(default=True)
    analytics = models.BooleanField(default=False)
    marketing = models.BooleanField(default=False)
    policy_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_cookie_consent"


class LegalAcceptance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="legal_acceptances"
    )
    document = models.CharField(max_length=20)
    version = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_legal_acceptance"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "document", "version"], name="legal_acceptance_once"
            )
        ]


class DataExportRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="data_exports"
    )
    status = models.CharField(max_length=20, default="ready")
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_data_export"


class DeletionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deletion_requests"
    )
    status = models.CharField(max_length=20, default="completed")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_deletion_request"
