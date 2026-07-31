"""
Serializers stay focused on validation and shaping — no business logic.
Anything stateful (checking passwords, writing audit logs, issuing
tokens) happens in services/, called from the view.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "mobile",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "date_of_birth",
            "profile_photo",
            "role",
            "status",
            "is_verified",
            "last_login",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "mobile",
            "role",
            "status",
            "is_verified",
            "last_login",
            "created_at",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "gender", "date_of_birth"]

    def validate_first_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("First name cannot be blank.")
        return value.strip()


class AvatarUploadSerializer(serializers.Serializer):
    profile_photo = serializers.ImageField(required=True)


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email address or mobile number.")
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email address or mobile number.")


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the current password."}
            )
        validate_password(attrs["new_password"])
        return attrs


class LoginHistorySerializer(serializers.Serializer):
    action = serializers.CharField()
    ip_address = serializers.IPAddressField(allow_null=True)
    user_agent = serializers.CharField()
    created_at = serializers.DateTimeField()
