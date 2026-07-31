import uuid
from django.conf import settings
from django.db import models

class DashboardPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dashboard_preference")
    dashboard_type = models.CharField(max_length=20, default="family")
    layout = models.JSONField(default=dict, blank=True)
    default_date_range = models.CharField(max_length=30, default="current_month")
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "dashboard_preference"

class AnalyticsCache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="analytics_caches")
    cache_key = models.CharField(max_length=255)
    payload = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "dashboard_analytics_cache"
        constraints = [models.UniqueConstraint(fields=["family", "cache_key"], name="dashboard_cache_key_per_family")]
        indexes = [models.Index(fields=["family", "expires_at"])]
