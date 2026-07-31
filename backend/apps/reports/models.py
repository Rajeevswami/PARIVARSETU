import uuid
from django.conf import settings
from django.db import models

class SavedReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="saved_reports")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_reports")
    name = models.CharField(max_length=150)
    report_type = models.CharField(max_length=30)
    filters = models.JSONField(default=dict, blank=True)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "reports_saved_report"; ordering = ["-updated_at"]

class ReportSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="report_schedules")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_schedules")
    saved_report = models.ForeignKey(SavedReport, null=True, blank=True, on_delete=models.SET_NULL, related_name="schedules")
    report_type = models.CharField(max_length=30)
    filters = models.JSONField(default=dict, blank=True)
    frequency = models.CharField(max_length=12, choices=[(x,x.title()) for x in ("daily","weekly","monthly","yearly")])
    recipients = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "reports_schedule"

class ReportExportHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="report_exports")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="report_exports")
    report_type = models.CharField(max_length=30)
    export_format = models.CharField(max_length=10)
    filters = models.JSONField(default=dict, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "reports_export_history"; ordering = ["-created_at"]
