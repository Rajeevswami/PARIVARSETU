from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PasswordResetToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = [
        "email",
        "get_full_name",
        "role",
        "status",
        "is_active",
        "is_verified",
        "created_at",
    ]
    list_filter = ["role", "status", "is_active", "is_verified", "is_deleted"]
    search_fields = ["email", "mobile", "first_name", "last_name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("id", "email", "mobile", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "gender", "date_of_birth", "profile_photo")},
        ),
        ("Family", {"fields": ("family", "household", "role")}),
        ("Status", {"fields": ("status", "is_active", "is_staff", "is_superuser", "is_verified")}),
        (
            "Audit",
            {"fields": ("created_at", "updated_at", "last_login", "is_deleted", "deleted_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "password1", "password2", "role"),
            },
        ),
    )
    filter_horizontal = ()


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at", "used_at"]
    readonly_fields = [f.name for f in PasswordResetToken._meta.fields]
    search_fields = ["user__email"]

    def has_add_permission(self, request):
        return False
