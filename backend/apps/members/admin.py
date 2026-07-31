from django.contrib import admin

from .models import Member, MemberInvitation


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "employee_code",
        "family",
        "household",
        "relationship",
        "status",
        "created_at",
    ]
    list_filter = ["status", "relationship", "gender", "is_deleted"]
    search_fields = ["display_name", "employee_code", "user__email", "family__family_name"]
    readonly_fields = ["id", "employee_code", "joining_date", "created_at", "updated_at"]
    autocomplete_fields = ["user", "family", "household"]
    ordering = ["-created_at"]


@admin.register(MemberInvitation)
class MemberInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "mobile", "family", "role", "status", "expires_at", "created_at"]
    list_filter = ["status", "role"]
    search_fields = ["email", "mobile", "family__family_name"]
    readonly_fields = ["id", "token", "created_at"]
    autocomplete_fields = ["family", "household", "invited_by"]
    ordering = ["-created_at"]
