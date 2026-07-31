from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountGroupViewSet,
    AccountStatementView,
    AdjustmentViewSet,
    BankBookView,
    CashBookView,
    FamilyFinancialSummaryView,
    FinancialPeriodViewSet,
    JournalRegisterExportView,
    JournalViewSet,
    LedgerAccountViewSet,
    TrialBalanceView,
)

app_name = "ledger"

router = DefaultRouter()
router.register("account-groups", AccountGroupViewSet, basename="account-group")
router.register("accounts", LedgerAccountViewSet, basename="ledger-account")
router.register("journals", JournalViewSet, basename="journal")
router.register("adjustments", AdjustmentViewSet, basename="adjustment")
router.register("financial-periods", FinancialPeriodViewSet, basename="financial-period")

urlpatterns = [
    path("trial-balance/", TrialBalanceView.as_view(), name="trial_balance"),
    path(
        "accounts/<uuid:account_id>/statement/",
        AccountStatementView.as_view(),
        name="account_statement",
    ),
    path("cash-book/", CashBookView.as_view(), name="cash_book"),
    path("bank-book/", BankBookView.as_view(), name="bank_book"),
    path("family-summary/", FamilyFinancialSummaryView.as_view(), name="family_summary"),
    path(
        "journal-register/export/",
        JournalRegisterExportView.as_view(),
        name="journal_register_export",
    ),
] + router.urls
