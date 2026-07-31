from django.contrib import admin

from .models import (
    InterestConfiguration,
    LedgerPostingQueue,
    Loan,
    LoanInstallment,
    LoanPayment,
    LoanType,
    Reminder,
)


class LoanInstallmentInline(admin.TabularInline):
    model = LoanInstallment
    extra = 0


@admin.register(LoanInstallment)
class LoanInstallmentAdmin(admin.ModelAdmin):
    list_display = ["loan", "installment_number", "due_date", "amount", "status"]
    list_filter = ["status"]
    search_fields = ["loan__loan_number", "loan__title"]
    autocomplete_fields = ["loan"]


class LoanPaymentInline(admin.TabularInline):
    model = LoanPayment
    extra = 0
    readonly_fields = ["payment_number", "created_at"]


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "status"]
    search_fields = ["name", "family__family_name"]
    autocomplete_fields = ["family"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        "loan_number",
        "title",
        "family",
        "borrower",
        "total_amount",
        "status",
        "loan_date",
    ]
    list_filter = ["status", "loan_source", "interest_type", "is_deleted"]
    search_fields = ["loan_number", "title", "family__family_name"]
    autocomplete_fields = ["family", "household", "borrower", "lender", "loan_type"]
    readonly_fields = ["id", "loan_number", "created_at", "updated_at"]
    inlines = [LoanInstallmentInline, LoanPaymentInline]
    ordering = ["-loan_date"]


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ["title", "reminder_type", "member", "remind_at", "status"]
    list_filter = ["reminder_type", "status"]
    autocomplete_fields = ["family", "loan", "installment", "member"]


@admin.register(InterestConfiguration)
class InterestConfigurationAdmin(admin.ModelAdmin):
    list_display = ["family", "loan_type", "interest_type", "default_rate"]
    autocomplete_fields = ["family", "loan_type"]


@admin.register(LedgerPostingQueue)
class LedgerPostingQueueAdmin(admin.ModelAdmin):
    list_display = ["event_type", "amount", "source_model", "status", "created_at"]
    list_filter = ["event_type", "status"]
    readonly_fields = [f.name for f in LedgerPostingQueue._meta.fields]

    def has_add_permission(self, request):
        return False
