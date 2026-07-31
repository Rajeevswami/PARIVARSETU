from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.common.response import success_response
from apps.audit.services.audit_service import record
from apps.expenses.models import Expense
from apps.loans.models import Loan
from apps.borrow_lend.models import BorrowTransaction, LendTransaction, Settlement
from apps.members.models import Member
from apps.households.models import Household
from .models import DashboardPreference

ZERO = Decimal("0")
def amount(queryset, field="amount"): return queryset.aggregate(value=Sum(field))["value"] or ZERO
def scope(request, qs, member_field=None):
    if request.user.role == "family_admin": return qs.filter(family_id=request.user.family_id)
    if member_field and hasattr(request.user, "member_profile"): return qs.filter(**{member_field: request.user.member_profile})
    return qs.filter(family_id=request.user.family_id)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        family_id = request.user.family_id
        if not family_id: return success_response(data={"kpis": {}, "recent": {}})
        today = date.today(); month_start = today.replace(day=1)
        expenses = scope(request, Expense.objects.filter(is_deleted=False), "paid_by")
        loans = scope(request, Loan.objects.filter(is_deleted=False), "borrower")
        borrows = scope(request, BorrowTransaction.objects.filter(is_deleted=False), "borrower")
        lends = scope(request, LendTransaction.objects.filter(is_deleted=False), "giver")
        monthly_expenses = expenses.filter(expense_date__gte=month_start)
        total_expenses = amount(expenses); total_loans = amount(loans.exclude(status__in=["completed", "cancelled"]), "remaining_amount")
        data = {"dashboard_type": "family" if request.user.role == "family_admin" else "member", "kpis": {
          "total_expenses": total_expenses, "total_income": ZERO, "net_balance": -total_expenses,
          "outstanding_loans": total_loans, "monthly_savings": -amount(monthly_expenses),
          "pending_settlements": amount(Settlement.objects.filter(member__family_id=family_id, status="recorded"), "remaining_amount"),
          "active_members": Member.objects.filter(family_id=family_id, status="active", is_deleted=False).count(),
          "households": Household.objects.filter(family_id=family_id, is_deleted=False).count(),
          "borrow_amount": amount(borrows), "lend_amount": amount(lends),
        }, "recent": {
          "expenses": list(expenses.order_by("-expense_date")[:5].values("id", "expense_number", "title", "amount", "expense_date")),
          "loans": list(loans.order_by("-loan_date")[:5].values("id", "loan_number", "title", "remaining_amount", "status")),
          "settlements": list(Settlement.objects.filter(member__family_id=family_id).order_by("-settlement_date")[:5].values("id", "amount", "settlement_date", "status")),
        }}
        record(actor=request.user, action="dashboard_viewed", family_id=family_id)
        return success_response(data=data)

class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        family_id = request.user.family_id
        expenses = scope(request, Expense.objects.filter(is_deleted=False), "paid_by")
        trends = expenses.annotate(period=TruncMonth("expense_date")).values("period").annotate(total=Sum("amount")).order_by("period")
        categories = expenses.values("category__name").annotate(total=Sum("amount")).order_by("-total")[:10]
        households = expenses.values("household__household_name").annotate(total=Sum("amount")).order_by("-total")[:10]
        data = {"expense_trends": list(trends), "category_analysis": list(categories), "household_comparison": list(households),
          "loan_trends": list(scope(request, Loan.objects.filter(is_deleted=False), "borrower").annotate(period=TruncMonth("loan_date")).values("period").annotate(total=Sum("principal_amount")).order_by("period")),
          "borrow_vs_lend": {"borrow": amount(scope(request, BorrowTransaction.objects.filter(is_deleted=False), "borrower")), "lend": amount(scope(request, LendTransaction.objects.filter(is_deleted=False), "giver"))}}
        record(actor=request.user, action="analytics_viewed", family_id=family_id)
        return success_response(data=data)

class PreferenceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        pref, _ = DashboardPreference.objects.get_or_create(user=request.user)
        return success_response(data={"dashboard_type": pref.dashboard_type, "layout": pref.layout, "default_date_range": pref.default_date_range})
    def patch(self, request):
        pref, _ = DashboardPreference.objects.get_or_create(user=request.user)
        for field in ("dashboard_type", "layout", "default_date_range"):
            if field in request.data: setattr(pref, field, request.data[field])
        pref.save(); return self.get(request)
