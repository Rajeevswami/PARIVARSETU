from django.contrib import admin

from .models import (
    Expense,
    ExpenseAttachment,
    ExpenseCategory,
    ExpenseComment,
    ExpenseParticipant,
    ExpenseSettlement,
    LedgerPostingQueue,
)


class ExpenseParticipantInline(admin.TabularInline):
    model = ExpenseParticipant
    extra = 0
    readonly_fields = ["id"]


class ExpenseAttachmentInline(admin.TabularInline):
    model = ExpenseAttachment
    extra = 0
    readonly_fields = ["checksum", "file_size", "created_at"]


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "status", "sort_order"]
    list_filter = ["status", "is_deleted"]
    search_fields = ["name", "family__family_name"]
    autocomplete_fields = ["family"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "expense_number",
        "title",
        "family",
        "amount",
        "status",
        "paid_by",
        "expense_date",
    ]
    list_filter = ["status", "payment_method", "visibility", "is_deleted"]
    search_fields = ["expense_number", "title", "family__family_name"]
    autocomplete_fields = ["family", "household", "category", "paid_by"]
    readonly_fields = ["id", "expense_number", "created_at", "updated_at"]
    inlines = [ExpenseParticipantInline, ExpenseAttachmentInline]
    ordering = ["-expense_date"]


@admin.register(ExpenseSettlement)
class ExpenseSettlementAdmin(admin.ModelAdmin):
    list_display = ["expense", "member", "paid_amount", "settlement_date", "status"]
    list_filter = ["status"]
    autocomplete_fields = ["expense", "member"]


@admin.register(ExpenseComment)
class ExpenseCommentAdmin(admin.ModelAdmin):
    list_display = ["expense", "member", "created_at"]
    autocomplete_fields = ["expense", "member"]


@admin.register(LedgerPostingQueue)
class LedgerPostingQueueAdmin(admin.ModelAdmin):
    list_display = ["expense", "event_type", "amount", "status", "created_at"]
    list_filter = ["event_type", "status"]
    readonly_fields = [f.name for f in LedgerPostingQueue._meta.fields]

    def has_add_permission(self, request):
        return False
