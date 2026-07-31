from django.contrib import admin

from .models import Household


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = [
        "household_name",
        "household_code",
        "family",
        "status",
        "head_of_household",
        "created_at",
    ]
    list_filter = ["status", "is_deleted"]
    search_fields = ["household_name", "household_code", "family__family_name"]
    readonly_fields = ["id", "household_code", "created_at", "updated_at"]
    autocomplete_fields = ["family", "head_of_household"]
    ordering = ["-created_at"]
