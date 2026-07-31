"""Views stay thin: parse/validate, call the appropriate service, shape the response."""

import csv
import io

from django.http import HttpResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsFamilyAdmin
from apps.common.response import error_response, success_response

from .models import AccountGroup, FinancialPeriod, Journal, LedgerAccount
from .permissions import IsFamilyAdminOrReadOnly
from .serializers import (
    AccountGroupSerializer,
    AdjustmentEntrySerializer,
    CreateAdjustmentSerializer,
    FinancialPeriodSerializer,
    JournalSerializer,
    LedgerAccountCreateSerializer,
    LedgerAccountSerializer,
    ManualJournalCreateSerializer,
)
from .services import (
    adjustment_service,
    balance_service,
    closing_service,
    journal_service,
    posting_service,
    statement_service,
)


class AccountGroupViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountGroupSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AccountGroup.objects.none()
        user = self.request.user
        if user.family_id is None:
            return AccountGroup.objects.none()
        return AccountGroup.objects.filter(family_id=user.family_id)

    def list(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_queryset(), many=True).data)


class LedgerAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["account_code", "account_name"]
    ordering = ["account_code"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LedgerAccount.objects.none()
        user = self.request.user
        if user.family_id is None:
            return LedgerAccount.objects.none()
        return LedgerAccount.objects.filter(family_id=user.family_id).select_related(
            "account_group", "balance"
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return LedgerAccountCreateSerializer
        return LedgerAccountSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [permissions.IsAuthenticated(), IsFamilyAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = LedgerAccount.objects.create(
            family_id=request.user.family_id, **serializer.validated_data
        )

        audit_services.record(
            actor=request.user,
            action=audit_services.AuditAction.LEDGER_ACCOUNT_CREATED,
            target_model="LedgerAccount",
            target_id=account.id,
            family_id=request.user.family_id,
        )
        return success_response(
            data=LedgerAccountSerializer(account).data, message="Account created", status_code=201
        )

    def partial_update(self, request, *args, **kwargs):
        account = self.get_object()
        if account.is_system_account and "account_code" in request.data:
            return error_response("System accounts' codes cannot be changed.", status_code=403)
        serializer = self.get_serializer(account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(account, field, value)
        account.save()
        return success_response(
            data=LedgerAccountSerializer(account).data, message="Account updated"
        )

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        return success_response(data=LedgerAccountSerializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=LedgerAccountSerializer(self.get_object()).data)


class JournalViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsFamilyAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["journal_number", "reference_type", "reference_id", "description"]
    ordering_fields = ["journal_date", "created_at"]
    ordering = ["-journal_date"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Journal.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Journal.objects.none()
        qs = Journal.objects.filter(family_id=user.family_id).prefetch_related(
            "entries__ledger_account"
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        transaction_type = self.request.query_params.get("transaction_type")
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(journal_date__gte=date_from)
        if date_to:
            qs = qs.filter(journal_date__lte=date_to)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ManualJournalCreateSerializer
        return JournalSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = [
            {
                "ledger_account": line["ledger_account"],
                "entry_type": line["entry_type"],
                "amount": line["amount"],
                "description": line.get("description", ""),
            }
            for line in serializer.validated_data["lines"]
        ]

        try:
            journal = journal_service.create_journal(
                family_id=request.user.family_id,
                transaction_type="manual_journal",
                journal_date=serializer.validated_data["journal_date"],
                lines=lines,
                description=serializer.validated_data.get("description", ""),
                created_by=request.user,
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=JournalSerializer(self.get_queryset().get(id=journal.id)).data,
            message="Journal created (draft)",
            status_code=201,
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response(JournalSerializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=JournalSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def post_entry(self, request, pk=None):
        journal = self.get_object()
        try:
            posting_service.post_journal(actor=request.user, journal=journal)
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=JournalSerializer(self.get_queryset().get(id=journal.id)).data,
            message="Journal posted",
        )


class AdjustmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsFamilyAdmin]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return None
        from .models import AdjustmentEntry

        user = self.request.user
        if user.family_id is None:
            return AdjustmentEntry.objects.none()
        return AdjustmentEntry.objects.filter(family_id=user.family_id)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateAdjustmentSerializer
        return AdjustmentEntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        original_journal = None
        if serializer.validated_data.get("original_journal"):
            original_journal = get_object_or_404(
                Journal,
                id=serializer.validated_data["original_journal"],
                family_id=request.user.family_id,
            )

        lines = [
            {
                "ledger_account": line["ledger_account"],
                "entry_type": line["entry_type"],
                "amount": line["amount"],
                "description": line.get("description", ""),
            }
            for line in serializer.validated_data["lines"]
        ]

        try:
            adjustment = adjustment_service.create_adjustment(
                actor=request.user,
                family_id=request.user.family_id,
                original_journal=original_journal,
                lines=lines,
                reason=serializer.validated_data["reason"],
                journal_date=serializer.validated_data["journal_date"],
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=AdjustmentEntrySerializer(adjustment).data,
            message="Adjustment posted",
            status_code=201,
        )

    def list(self, request, *args, **kwargs):
        return success_response(data=AdjustmentEntrySerializer(self.get_queryset(), many=True).data)


class FinancialPeriodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FinancialPeriodSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FinancialPeriod.objects.none()
        user = self.request.user
        if user.family_id is None:
            return FinancialPeriod.objects.none()
        return FinancialPeriod.objects.filter(family_id=user.family_id)

    def list(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_queryset(), many=True).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsFamilyAdmin],
    )
    def close(self, request, pk=None):
        period = self.get_object()
        try:
            closing_service.close_period(actor=request.user, period=period)
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(data=self.get_serializer(period).data, message="Period closed")


class TrialBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return success_response(data=balance_service.get_trial_balance(request.user.family_id))


class AccountStatementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, account_id):
        try:
            data = statement_service.account_statement(
                family_id=request.user.family_id,
                account_id=account_id,
                date_from=request.query_params.get("date_from"),
                date_to=request.query_params.get("date_to"),
            )
        except LedgerAccount.DoesNotExist:
            return error_response("Account not found.", status_code=404)
        return success_response(data=data)


class CashBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = statement_service.cash_book(
            family_id=request.user.family_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return success_response(data=data)


class BankBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = statement_service.bank_book(
            family_id=request.user.family_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return success_response(data=data)


class FamilyFinancialSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        family_id = request.user.family_id
        return success_response(
            data={
                "family_balance": str(balance_service.get_family_balance(family_id)),
                "household_balance": str(balance_service.get_household_balance(family_id)),
                "cash_and_bank": balance_service.get_cash_and_bank_summary(family_id),
                "income_expense": balance_service.get_income_expense_summary(family_id),
            }
        )


class JournalRegisterExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        journals = statement_service.journal_register(
            family_id=request.user.family_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
            status=request.query_params.get("status"),
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Journal Number", "Date", "Type", "Description", "Status"])
        for j in journals:
            writer.writerow(
                [j.journal_number, j.journal_date, j.transaction_type, j.description, j.status]
            )

        audit_services.record(
            actor=request.user,
            action=audit_services.AuditAction.LEDGER_STATEMENT_EXPORTED,
            target_model="JournalRegister",
            target_id="",
            family_id=request.user.family_id,
        )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="journal_register.csv"'
        return response
