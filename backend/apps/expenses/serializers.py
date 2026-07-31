from decimal import Decimal

from rest_framework import serializers

from apps.households.models import Household
from apps.members.models import Member

from .models import (
    Expense,
    ExpenseAttachment,
    ExpenseCategory,
    ExpenseComment,
    ExpenseParticipant,
    ExpenseSettlement,
)
from .services.splits import SplitType


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "color",
            "sort_order",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExpenseCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "description", "icon", "color", "sort_order"]

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be blank.")

        request = self.context.get("request")
        if request is not None and request.user.family_id is not None:
            qs = ExpenseCategory.objects.filter(
                family_id=request.user.family_id, name__iexact=value, is_deleted=False
            )
            if self.instance is not None:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError("A category with this name already exists.")
        return value


class ExpenseParticipantSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)

    class Meta:
        model = ExpenseParticipant
        fields = [
            "id",
            "member",
            "member_name",
            "share_amount",
            "share_percentage",
            "settled_amount",
            "pending_amount",
            "status",
        ]
        read_only_fields = fields


class ExpenseAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAttachment
        fields = [
            "id",
            "file",
            "file_name",
            "mime_type",
            "file_size",
            "checksum",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = fields


class ExpenseCommentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)

    class Meta:
        model = ExpenseComment
        fields = ["id", "member", "member_name", "comment", "created_at"]
        read_only_fields = ["id", "member", "member_name", "created_at"]


class ExpenseCommentCreateSerializer(serializers.Serializer):
    comment = serializers.CharField(max_length=2000)


class ExpenseSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSettlement
        fields = [
            "id",
            "member",
            "paid_amount",
            "received_amount",
            "remaining_amount",
            "settlement_date",
            "remarks",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    paid_by_name = serializers.CharField(source="paid_by.display_name", read_only=True)
    household_name = serializers.CharField(
        source="household.household_name", read_only=True, default=None
    )
    participants = ExpenseParticipantSerializer(many=True, read_only=True)
    attachments = ExpenseAttachmentSerializer(many=True, read_only=True)
    settlements = ExpenseSettlementSerializer(many=True, read_only=True)
    total_settled = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id",
            "expense_number",
            "household",
            "household_name",
            "category",
            "category_name",
            "title",
            "description",
            "expense_date",
            "amount",
            "currency",
            "paid_by",
            "paid_by_name",
            "payment_method",
            "visibility",
            "status",
            "reference_number",
            "notes",
            "participants",
            "attachments",
            "settlements",
            "total_settled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "expense_number", "status", "created_at", "updated_at"]

    def get_total_settled(self, obj: Expense) -> str:
        return str(sum((p.settled_amount for p in obj.participants.all()), obj.amount * 0))


class ParticipantInputSerializer(serializers.Serializer):
    member_id = serializers.UUIDField()
    value = serializers.DecimalField(
        max_digits=12,
        decimal_places=4,
        required=False,
        help_text="Percentage or fixed amount, per split_type",
    )


class ExpenseCreateSerializer(serializers.Serializer):
    household = serializers.PrimaryKeyRelatedField(
        queryset=Household.objects.all(), required=False, allow_null=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=ExpenseCategory.objects.all(), required=False, allow_null=True
    )
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    expense_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.CharField(max_length=3, required=False, default="INR")
    paid_by = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    payment_method = serializers.ChoiceField(
        choices=["cash", "bank", "upi", "card", "wallet", "cheque"]
    )
    visibility = serializers.ChoiceField(
        choices=["private", "household", "family"], default="household"
    )
    reference_number = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    split_type = serializers.ChoiceField(choices=list(SplitType.ALL))
    participants = ParticipantInputSerializer(many=True)

    def validate_title(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        split_type = attrs["split_type"]
        needs_value = split_type in ("percentage", "fixed", "custom")
        for p in attrs["participants"]:
            if needs_value and p.get("value") is None:
                message = f"'value' is required for each participant (split_type={split_type})."
                raise serializers.ValidationError({"participants": message})
        return attrs


class ExpenseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "household",
            "category",
            "title",
            "description",
            "expense_date",
            "payment_method",
            "visibility",
            "reference_number",
            "notes",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}


class RecordSettlementSerializer(serializers.Serializer):
    member_id = serializers.UUIDField()
    paid_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    settlement_date = serializers.DateField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
