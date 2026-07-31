from decimal import Decimal

from rest_framework import serializers

from apps.households.models import Household
from apps.members.models import Member

from .models import BorrowTransaction, LendTransaction, Settlement


class BorrowTransactionSerializer(serializers.ModelSerializer):
    borrower_name = serializers.CharField(source="borrower.display_name", read_only=True)
    lender_name = serializers.CharField(source="lender.display_name", read_only=True, default=None)
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, default=None
    )
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = BorrowTransaction
        fields = [
            "id",
            "transaction_number",
            "household",
            "household_name",
            "borrower",
            "borrower_name",
            "lender",
            "lender_name",
            "external_lender_name",
            "amount",
            "date",
            "reason",
            "payment_method",
            "status",
            "settled_amount",
            "remaining_amount",
            "created_at",
        ]
        read_only_fields = ["id", "transaction_number", "status", "settled_amount", "created_at"]


class BorrowTransactionCreateSerializer(serializers.Serializer):
    household = serializers.PrimaryKeyRelatedField(
        queryset=Household.objects.all(), required=False, allow_null=True
    )
    borrower = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    lender = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), required=False, allow_null=True
    )
    external_lender_name = serializers.CharField(required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    payment_method = serializers.ChoiceField(
        choices=["cash", "bank", "upi", "card", "wallet", "cheque"]
    )


class LendTransactionSerializer(serializers.ModelSerializer):
    giver_name = serializers.CharField(source="giver.display_name", read_only=True)
    receiver_name = serializers.CharField(
        source="receiver.display_name", read_only=True, default=None
    )
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, default=None
    )
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LendTransaction
        fields = [
            "id",
            "transaction_number",
            "household",
            "household_name",
            "giver",
            "giver_name",
            "receiver",
            "receiver_name",
            "external_receiver_name",
            "amount",
            "date",
            "reason",
            "payment_method",
            "status",
            "settled_amount",
            "remaining_amount",
            "created_at",
        ]
        read_only_fields = ["id", "transaction_number", "status", "settled_amount", "created_at"]


class LendTransactionCreateSerializer(serializers.Serializer):
    household = serializers.PrimaryKeyRelatedField(
        queryset=Household.objects.all(), required=False, allow_null=True
    )
    giver = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    receiver = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), required=False, allow_null=True
    )
    external_receiver_name = serializers.CharField(required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    payment_method = serializers.ChoiceField(
        choices=["cash", "bank", "upi", "card", "wallet", "cheque"]
    )


class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = [
            "id",
            "reference_type",
            "reference_id",
            "member",
            "amount",
            "settled_amount",
            "remaining_amount",
            "status",
            "settlement_date",
            "remarks",
            "created_at",
        ]
        read_only_fields = fields


class RecordSettlementSerializer(serializers.Serializer):
    reference_type = serializers.ChoiceField(choices=["borrow", "lend"])
    reference_id = serializers.UUIDField()
    member_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    settlement_date = serializers.DateField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
