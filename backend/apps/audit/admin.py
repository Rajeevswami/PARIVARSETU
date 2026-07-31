from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_model", "family_id", "created_at")
    list_filter = ("action",)
    search_fields = ("actor__email", "target_model", "target_id")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
