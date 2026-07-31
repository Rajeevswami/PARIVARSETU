from decimal import Decimal

from rest_framework import serializers

from apps.households.models import Household
from apps.members.models import Member

from .models import InterestConfiguration, Loan, LoanInstallment, LoanPayment, LoanType, Reminder


class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = ["id", "name", "description", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class LoanTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = ["name", "description"]

    def validate_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return value.strip()


class LoanInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanInstallment
        fields = ["id", "installment_number", "due_date", "amount", "paid_amount", "status"]
        read_only_fields = fields


class LoanPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanPayment
        fields = [
            "id",
            "payment_number",
            "payment_date",
            "amount",
            "interest_paid",
            "principal_paid",
            "remaining_balance",
            "payment_method",
            "remarks",
            "attachment",
            "created_at",
        ]
        read_only_fields = fields


class LoanSerializer(serializers.ModelSerializer):
    borrower_name = serializers.CharField(source="borrower.display_name", read_only=True)
    lender_name = serializers.CharField(source="lender.display_name", read_only=True, default=None)
    loan_type_name = serializers.CharField(source="loan_type.name", read_only=True, default=None)
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, default=None
    )
    installments = LoanInstallmentSerializer(many=True, read_only=True)
    payments = LoanPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_number",
            "household",
            "household_name",
            "borrower",
            "borrower_name",
            "loan_source",
            "lender",
            "lender_name",
            "external_lender_name",
            "loan_type",
            "loan_type_name",
            "title",
            "description",
            "principal_amount",
            "interest_rate",
            "interest_type",
            "interest_amount",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "loan_date",
            "due_date",
            "status",
            "allow_overpayment",
            "installments",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "loan_number",
            "interest_amount",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "status",
            "created_at",
            "updated_at",
        ]


class LoanCreateSerializer(serializers.Serializer):
    household = serializers.PrimaryKeyRelatedField(
        queryset=Household.objects.all(), required=False, allow_null=True
    )
    borrower = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    loan_source = serializers.ChoiceField(choices=["internal", "external"], default="internal")
    lender = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), required=False, allow_null=True
    )
    external_lender_name = serializers.CharField(required=False, allow_blank=True, default="")
    loan_type = serializers.PrimaryKeyRelatedField(
        queryset=LoanType.objects.all(), required=False, allow_null=True
    )
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    principal_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    interest_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=Decimal("0")
    )
    interest_type = serializers.ChoiceField(choices=["none", "simple", "compound"], default="none")
    loan_date = serializers.DateField()
    due_date = serializers.DateField(required=False, allow_null=True)
    allow_overpayment = serializers.BooleanField(required=False, default=False)

    def validate_title(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value.strip()


class LoanUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ["household", "loan_type", "title", "description", "due_date", "allow_overpayment"]
        extra_kwargs = {field: {"required": False} for field in fields}


class RecordPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_date = serializers.DateField()
    payment_method = serializers.ChoiceField(
        choices=["cash", "bank", "upi", "card", "wallet", "cheque"]
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.FileField(required=False, allow_null=True)


class ReminderSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)

    class Meta:
        model = Reminder
        fields = [
            "id",
            "loan",
            "installment",
            "member",
            "reminder_type",
            "member_name",
            "title",
            "message",
            "remind_at",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class ReminderCreateSerializer(serializers.Serializer):
    loan = serializers.PrimaryKeyRelatedField(
        queryset=Loan.objects.all(), required=False, allow_null=True
    )
    installment = serializers.PrimaryKeyRelatedField(
        queryset=LoanInstallment.objects.all(), required=False, allow_null=True
    )
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    reminder_type = serializers.ChoiceField(
        choices=["due_date", "overdue", "installment", "custom"]
    )
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(required=False, allow_blank=True, default="")
    remind_at = serializers.DateTimeField()


class InterestConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestConfiguration
        fields = [
            "id",
            "loan_type",
            "interest_type",
            "default_rate",
            "compounding_frequency",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
