from decimal import Decimal

from rest_framework import serializers

from .models import (
    AccountGroup,
    AdjustmentEntry,
    FinancialPeriod,
    Journal,
    JournalEntry,
    LedgerAccount,
    LedgerEntry,
)


class AccountGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        fields = ["id", "name", "normal_balance", "sort_order"]
        read_only_fields = fields


class LedgerAccountSerializer(serializers.ModelSerializer):
    account_group_name = serializers.CharField(source="account_group.name", read_only=True)
    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = LedgerAccount
        fields = [
            "id",
            "account_code",
            "account_name",
            "account_group",
            "account_group_name",
            "parent_account",
            "description",
            "status",
            "is_system_account",
            "current_balance",
            "created_at",
        ]
        read_only_fields = ["id", "is_system_account", "created_at"]

    def get_current_balance(self, obj: LedgerAccount) -> str:
        balance = getattr(obj, "balance", None)
        return str(balance.current_balance) if balance else "0.00"


class LedgerAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAccount
        fields = ["account_code", "account_name", "account_group", "parent_account", "description"]

    def validate_account_code(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Account code cannot be blank.")
        return value.strip()


class JournalEntrySerializer(serializers.ModelSerializer):
    ledger_account_name = serializers.CharField(
        source="ledger_account.account_name", read_only=True
    )

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "ledger_account",
            "ledger_account_name",
            "entry_type",
            "amount",
            "description",
            "sequence",
        ]
        read_only_fields = fields


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "ledger_number",
            "ledger_account",
            "transaction_date",
            "opening_balance",
            "debit",
            "credit",
            "closing_balance",
            "reference_number",
            "remarks",
        ]
        read_only_fields = fields


class JournalSerializer(serializers.ModelSerializer):
    entries = JournalEntrySerializer(many=True, read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()

    class Meta:
        model = Journal
        fields = [
            "id",
            "journal_number",
            "transaction_type",
            "reference_type",
            "reference_id",
            "journal_date",
            "description",
            "status",
            "entries",
            "total_debit",
            "total_credit",
            "created_at",
            "posted_at",
        ]
        read_only_fields = fields

    def get_total_debit(self, obj: Journal) -> str:
        return str(
            sum((e.amount for e in obj.entries.all() if e.entry_type == "debit"), Decimal("0"))
        )

    def get_total_credit(self, obj: Journal) -> str:
        return str(
            sum((e.amount for e in obj.entries.all() if e.entry_type == "credit"), Decimal("0"))
        )


class ManualJournalLineSerializer(serializers.Serializer):
    ledger_account = serializers.UUIDField()
    entry_type = serializers.ChoiceField(choices=["debit", "credit"])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    description = serializers.CharField(required=False, allow_blank=True, default="")


class ManualJournalCreateSerializer(serializers.Serializer):
    journal_date = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    lines = ManualJournalLineSerializer(many=True)

    def validate_lines(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "A journal needs at least two lines (one debit, one credit)."
            )
        return value


class FinancialPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPeriod
        fields = ["id", "name", "start_date", "end_date", "status", "created_at"]
        read_only_fields = fields


class AdjustmentEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdjustmentEntry
        fields = ["id", "original_journal", "adjustment_journal", "reason", "created_at"]
        read_only_fields = fields


class CreateAdjustmentSerializer(serializers.Serializer):
    original_journal = serializers.UUIDField(required=False, allow_null=True)
    journal_date = serializers.DateField()
    reason = serializers.CharField()
    lines = ManualJournalLineSerializer(many=True)

    def validate_lines(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("An adjustment needs at least two lines.")
        return value
