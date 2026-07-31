from django.contrib import admin

from .models import BorrowTransaction, LendTransaction, Settlement


@admin.register(BorrowTransaction)
class BorrowTransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_number", "family", "borrower", "amount", "status", "date"]
    list_filter = ["status", "payment_method", "is_deleted"]
    search_fields = ["transaction_number", "family__family_name"]
    autocomplete_fields = ["family", "household", "borrower", "lender"]
    readonly_fields = ["id", "transaction_number", "created_at", "updated_at"]


@admin.register(LendTransaction)
class LendTransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_number", "family", "giver", "amount", "status", "date"]
    list_filter = ["status", "payment_method", "is_deleted"]
    search_fields = ["transaction_number", "family__family_name"]
    autocomplete_fields = ["family", "household", "giver", "receiver"]
    readonly_fields = ["id", "transaction_number", "created_at", "updated_at"]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = [
        "reference_type",
        "reference_id",
        "member",
        "amount",
        "status",
        "settlement_date",
    ]
    list_filter = ["reference_type", "status"]
    autocomplete_fields = ["member"]
    readonly_fields = ["id", "created_at"]
