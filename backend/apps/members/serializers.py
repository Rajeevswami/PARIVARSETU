from rest_framework import serializers

from apps.households.models import Household

from .models import Member, MemberInvitation


class MemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, default=None
    )

    class Meta:
        model = Member
        fields = [
            "id",
            "user",
            "email",
            "role",
            "family",
            "household",
            "household_name",
            "employee_code",
            "display_name",
            "relationship",
            "gender",
            "blood_group",
            "marital_status",
            "occupation",
            "date_of_birth",
            "joining_date",
            "photo",
            "aadhaar_number_ready",
            "pan_number_ready",
            "emergency_contact",
            "notes",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "user", "family", "employee_code", "joining_date", "created_at"]


class MemberCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField()
    household_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Member
        fields = [
            "user_id",
            "household_id",
            "display_name",
            "relationship",
            "gender",
            "blood_group",
            "marital_status",
            "occupation",
            "date_of_birth",
            "emergency_contact",
            "notes",
        ]

    def validate_household_id(self, value):
        if value is None:
            return None
        if not Household.objects.filter(id=value).exists():
            raise serializers.ValidationError("Household not found.")
        return value


class MemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "display_name",
            "relationship",
            "gender",
            "blood_group",
            "marital_status",
            "occupation",
            "date_of_birth",
            "aadhaar_number_ready",
            "pan_number_ready",
            "emergency_contact",
            "notes",
            "status",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}


class TransferMemberSerializer(serializers.Serializer):
    household_id = serializers.UUIDField(allow_null=True, required=True)


class MemberInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberInvitation
        fields = [
            "id",
            "family",
            "household",
            "email",
            "mobile",
            "role",
            "relationship",
            "status",
            "created_at",
            "expires_at",
        ]
        read_only_fields = ["id", "family", "status", "created_at", "expires_at"]


class MemberInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_null=True)
    mobile = serializers.CharField(required=False, allow_null=True)
    household = serializers.PrimaryKeyRelatedField(
        queryset=Household.objects.all(), required=False, allow_null=True
    )
    role = serializers.ChoiceField(
        choices=["family_admin", "member", "future_ready", "read_only", "auditor"], default="member"
    )
    relationship = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("email") and not attrs.get("mobile"):
            raise serializers.ValidationError("Provide an email or a mobile number.")
        return attrs


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    first_name = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True, trim_whitespace=False)


class RejectInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
