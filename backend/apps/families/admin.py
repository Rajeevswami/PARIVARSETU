from django.contrib import admin

from .models import Family


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = [
        "family_name",
        "family_code",
        "subscription_plan",
        "status",
        "city",
        "created_at",
    ]
    list_filter = ["status", "subscription_plan", "subscription_status", "is_deleted"]
    search_fields = ["family_name", "family_code", "city", "state"]
    readonly_fields = ["id", "family_code", "created_at", "updated_at"]
    ordering = ["-created_at"]
