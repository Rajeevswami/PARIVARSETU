from rest_framework import serializers

from .models import Household


class HouseholdSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    head_of_household_name = serializers.CharField(
        source="head_of_household.display_name", read_only=True, default=None
    )

    class Meta:
        model = Household
        fields = [
            "id",
            "family",
            "household_name",
            "household_code",
            "description",
            "head_of_household",
            "head_of_household_name",
            "address",
            "contact_number",
            "status",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "family", "household_code", "created_at", "updated_at"]


class HouseholdCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = ["household_name", "description", "address", "contact_number"]

    def validate_household_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Household name cannot be blank.")
        return value.strip()


class HouseholdUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = ["household_name", "description", "address", "contact_number", "status"]
        extra_kwargs = {field: {"required": False} for field in fields}


class ChangeHeadSerializer(serializers.Serializer):
    member_id = serializers.UUIDField()
