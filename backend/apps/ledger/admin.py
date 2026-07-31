from django.contrib import admin

from .models import (
    AccountBalance,
    AccountGroup,
    AdjustmentEntry,
    ClosingPeriod,
    FinancialPeriod,
    Journal,
    JournalEntry,
    LedgerAccount,
    LedgerEntry,
    OpeningBalance,
)


class JournalEntryInline(admin.TabularInline):
    model = JournalEntry
    extra = 0


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "normal_balance", "sort_order"]
    search_fields = ["name", "family__family_name"]
    autocomplete_fields = ["family"]


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = [
        "account_code",
        "account_name",
        "family",
        "account_group",
        "status",
        "is_system_account",
    ]
    list_filter = ["status", "is_system_account"]
    search_fields = ["account_code", "account_name", "family__family_name"]
    autocomplete_fields = ["family", "account_group", "parent_account"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ["journal_number", "family", "transaction_type", "status", "journal_date"]
    list_filter = ["status", "transaction_type"]
    search_fields = ["journal_number", "reference_type", "reference_id", "family__family_name"]
    autocomplete_fields = ["family"]
    readonly_fields = ["id", "journal_number", "created_at", "posted_at"]
    inlines = [JournalEntryInline]
    ordering = ["-journal_date"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        "ledger_number",
        "ledger_account",
        "transaction_date",
        "debit",
        "credit",
        "closing_balance",
    ]
    search_fields = ["ledger_number", "reference_number"]
    autocomplete_fields = ["journal", "ledger_account"]
    readonly_fields = [f.name for f in LedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ["account", "opening_balance", "debit_total", "credit_total", "current_balance"]
    autocomplete_fields = ["account"]
    readonly_fields = [f.name for f in AccountBalance._meta.fields]


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ["ledger_account", "financial_period", "amount", "entry_type"]
    autocomplete_fields = ["family", "ledger_account", "financial_period"]


@admin.register(AdjustmentEntry)
class AdjustmentEntryAdmin(admin.ModelAdmin):
    list_display = ["reason", "family", "original_journal", "adjustment_journal", "created_at"]
    autocomplete_fields = ["family", "original_journal", "adjustment_journal"]
    readonly_fields = ["id", "created_at"]


@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "start_date", "end_date", "status"]
    list_filter = ["status"]
    search_fields = ["name", "family__family_name"]
    autocomplete_fields = ["family"]


@admin.register(ClosingPeriod)
class ClosingPeriodAdmin(admin.ModelAdmin):
    list_display = ["financial_period", "family", "closed_by", "closed_at"]
    autocomplete_fields = ["family", "financial_period"]
    readonly_fields = ["id", "closing_balances_snapshot", "closed_at"]
