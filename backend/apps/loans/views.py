"""Views stay thin: parse/validate, call the appropriate service, shape the response."""

import csv
import io

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsFamilyAdmin
from apps.common.response import error_response, success_response

from .models import Loan, LoanType, Reminder
from .permissions import CanEditLoan, CanViewLoan, IsFamilyAdminForDestructive
from .serializers import (
    InterestConfigurationSerializer,
    LoanCreateSerializer,
    LoanSerializer,
    LoanTypeCreateSerializer,
    LoanTypeSerializer,
    LoanUpdateSerializer,
    RecordPaymentSerializer,
    ReminderCreateSerializer,
    ReminderSerializer,
)
from .services import loan_service, payment_service, reminder_service


class LoanTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LoanType.objects.none()
        user = self.request.user
        if user.family_id is None:
            return LoanType.objects.none()
        return LoanType.objects.filter(family_id=user.family_id, is_deleted=False)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return LoanTypeCreateSerializer
        return LoanTypeSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [permissions.IsAuthenticated(), IsFamilyAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_type = LoanType.objects.create(
            family_id=request.user.family_id,
            created_by=request.user,
            updated_by=request.user,
            **serializer.validated_data,
        )
        return success_response(
            data=LoanTypeSerializer(loan_type).data, message="Loan type created", status_code=201
        )

    def list(self, request, *args, **kwargs):
        return success_response(data=LoanTypeSerializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=LoanTypeSerializer(self.get_object()).data)


class LoanViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "loan_type", "household", "borrower", "lender"]
    search_fields = ["loan_number", "title", "borrower__display_name", "lender__display_name"]
    ordering_fields = ["loan_date", "principal_amount", "total_amount", "title", "created_at"]
    ordering = ["-loan_date"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Loan.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Loan.objects.none()
        return (
            Loan.objects.filter(family_id=user.family_id, is_deleted=False)
            .select_related("borrower", "lender", "loan_type", "household")
            .prefetch_related("installments", "payments")
        )

    def get_list_queryset(self):
        qs = self.get_queryset()
        user = self.request.user
        if user.role == "family_admin":
            return qs
        member = getattr(user, "member_profile", None)
        if member is None:
            return qs.none()
        return qs.filter(Q(borrower=member) | Q(lender=member))

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        request = self.request
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(loan_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(loan_date__lte=date_to)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        if self.action in ("update", "partial_update"):
            return LoanUpdateSerializer
        return LoanSerializer

    def get_permissions(self):
        if self.action in ("destroy", "restore"):
            return [permissions.IsAuthenticated(), IsFamilyAdminForDestructive()]
        if self.action in ("update", "partial_update"):
            return [permissions.IsAuthenticated(), CanEditLoan()]
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), CanViewLoan()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            loan = loan_service.create_loan(
                actor=request.user,
                family_id=request.user.family_id,
                data=dict(serializer.validated_data),
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=LoanSerializer(self.get_queryset().get(id=loan.id)).data,
            message="Loan created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        loan = self.get_object()
        serializer = self.get_serializer(loan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        loan = loan_service.update_loan(
            actor=request.user, loan=loan, data=serializer.validated_data
        )
        return success_response(
            data=LoanSerializer(self.get_queryset().get(id=loan.id)).data, message="Loan updated"
        )

    def destroy(self, request, *args, **kwargs):
        loan = self.get_object()
        loan_service.cancel_loan(actor=request.user, loan=loan)
        return success_response(message="Loan cancelled")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_list_queryset()))
        return self.get_paginated_response(LoanSerializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=LoanSerializer(self.get_object()).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsFamilyAdminForDestructive],
    )
    def restore(self, request, pk=None):
        loan = get_object_or_404(Loan, id=pk, family_id=request.user.family_id)
        loan_service.restore_loan(actor=request.user, loan=loan)
        return success_response(data=LoanSerializer(loan).data, message="Loan restored")

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def payments(self, request, pk=None):
        loan = self.get_object()
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = payment_service.record_payment(
                actor=request.user, loan=loan, **serializer.validated_data
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        from .serializers import LoanPaymentSerializer

        return success_response(
            data=LoanPaymentSerializer(payment).data, message="Payment recorded", status_code=201
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.filter_queryset(self.get_list_queryset())
        by_status = list(
            qs.values("status")
            .annotate(total=Sum("total_amount"), count=Count("id"))
            .order_by("-total")
        )
        by_type = list(
            qs.values("loan_type__name").annotate(total=Sum("total_amount")).order_by("-total")
        )
        outstanding = (
            qs.exclude(status__in=["completed", "cancelled"]).aggregate(
                total=Sum("remaining_amount")
            )["total"]
            or 0
        )
        grand_total = qs.aggregate(total=Sum("total_amount"))["total"] or 0

        return success_response(
            data={
                "grand_total": str(grand_total),
                "outstanding_total": str(outstanding),
                "by_status": by_status,
                "by_type": by_type,
            }
        )

    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_list_queryset())
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Loan Number",
                "Title",
                "Borrower",
                "Lender",
                "Principal",
                "Total",
                "Paid",
                "Remaining",
                "Status",
                "Loan Date",
            ]
        )
        for loan in qs:
            writer.writerow(
                [
                    loan.loan_number,
                    loan.title,
                    loan.borrower.display_name,
                    loan.lender.display_name if loan.lender else loan.external_lender_name,
                    loan.principal_amount,
                    loan.total_amount,
                    loan.paid_amount,
                    loan.remaining_amount,
                    loan.status,
                    loan.loan_date,
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="loans.csv"'
        return response


class ReminderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Reminder.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Reminder.objects.none()
        qs = Reminder.objects.filter(family_id=user.family_id).select_related("member", "loan")
        if user.role == "family_admin":
            return qs
        member = getattr(user, "member_profile", None)
        return qs.filter(member=member) if member else qs.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReminderCreateSerializer
        return ReminderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reminder = reminder_service.create_reminder(
            actor=request.user, family_id=request.user.family_id, data=serializer.validated_data
        )
        return success_response(
            data=ReminderSerializer(reminder).data, message="Reminder created", status_code=201
        )

    def list(self, request, *args, **kwargs):
        return success_response(data=ReminderSerializer(self.get_queryset(), many=True).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        reminder = get_object_or_404(self.get_queryset(), id=pk)
        reminder_service.dismiss_reminder(actor=request.user, reminder=reminder)
        return success_response(message="Reminder dismissed")


class InterestConfigurationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InterestConfigurationSerializer

    def get(self, request):
        from .models import InterestConfiguration

        configs = InterestConfiguration.objects.filter(family_id=request.user.family_id)
        return success_response(data=InterestConfigurationSerializer(configs, many=True).data)

    def post(self, request):
        if request.user.role != "family_admin":
            return error_response(
                "Only a family admin can configure interest defaults.", status_code=403
            )

        from .models import InterestConfiguration

        serializer = InterestConfigurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = InterestConfiguration.objects.create(
            family_id=request.user.family_id, **serializer.validated_data
        )
        return success_response(
            data=InterestConfigurationSerializer(config).data,
            message="Interest configuration saved",
            status_code=201,
        )
