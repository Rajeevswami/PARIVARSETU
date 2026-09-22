from rest_framework import serializers

from .models import BillingProvider, PlanCode


class CheckoutSerializer(serializers.Serializer):
    plan_code = serializers.ChoiceField(choices=PlanCode.choices)
    provider = serializers.ChoiceField(choices=BillingProvider.choices)
    success_url = serializers.URLField(required=False)


class ConfirmCheckoutSerializer(serializers.Serializer):
    checkout_id = serializers.UUIDField()
