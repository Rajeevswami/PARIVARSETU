from rest_framework import serializers


class ConsentSerializer(serializers.Serializer):
    anonymous_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    analytics = serializers.BooleanField(default=False)
    marketing = serializers.BooleanField(default=False)


class AcceptanceSerializer(serializers.Serializer):
    document = serializers.ChoiceField(choices=["terms", "privacy"])


class DeletionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    confirm = serializers.BooleanField()

    def validate_confirm(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Confirm deletion to continue.")
        return value
