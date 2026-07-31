from rest_framework import serializers

from .models import Family


class FamilySerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    household_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Family
        fields = [
            "id",
            "family_name",
            "family_code",
            "description",
            "logo",
            "country",
            "state",
            "city",
            "currency",
            "language",
            "timezone",
            "subscription_plan",
            "subscription_status",
            "status",
            "member_count",
            "household_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "family_code",
            "subscription_plan",
            "subscription_status",
            "created_at",
            "updated_at",
        ]


class FamilyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = [
            "family_name",
            "description",
            "country",
            "state",
            "city",
            "currency",
            "language",
            "timezone",
        ]

    def validate_family_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Family name cannot be blank.")
        return value.strip()


class FamilyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = [
            "family_name",
            "description",
            "logo",
            "country",
            "state",
            "city",
            "currency",
            "language",
            "timezone",
            "status",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}
