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
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsFamilyAdmin
from apps.common.response import error_response, success_response

from .models import Expense, ExpenseCategory, ExpenseComment
from .permissions import CanEditExpense, CanViewExpense, IsFamilyAdminForDestructive
from .serializers import (
    ExpenseAttachmentSerializer,
    ExpenseCategoryCreateSerializer,
    ExpenseCategorySerializer,
    ExpenseCommentCreateSerializer,
    ExpenseCommentSerializer,
    ExpenseCreateSerializer,
    ExpenseSerializer,
    ExpenseSettlementSerializer,
    ExpenseUpdateSerializer,
    RecordSettlementSerializer,
)
from .services import attachment_service, category_service, expense_service, settlement_service


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ExpenseCategory.objects.none()
        user = self.request.user
        if user.family_id is None:
            return ExpenseCategory.objects.none()
        return ExpenseCategory.objects.filter(family_id=user.family_id, is_deleted=False)

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCategoryCreateSerializer
        if self.action in ("update", "partial_update"):
            return ExpenseCategoryCreateSerializer
        return ExpenseCategorySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [permissions.IsAuthenticated(), IsFamilyAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = category_service.create_category(
            actor=request.user, family_id=request.user.family_id, data=serializer.validated_data
        )
        return success_response(
            data=ExpenseCategorySerializer(category).data,
            message="Category created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = category_service.update_category(
            actor=request.user, category=category, data=serializer.validated_data
        )
        return success_response(
            data=ExpenseCategorySerializer(category).data, message="Category updated"
        )

    def list(self, request, *args, **kwargs):
        return success_response(data=ExpenseCategorySerializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=ExpenseCategorySerializer(self.get_object()).data)


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "payment_method", "paid_by", "household", "category"]
    search_fields = ["expense_number", "title", "category__name"]
    ordering_fields = ["expense_date", "amount", "title", "created_at"]
    ordering = ["-expense_date"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """
        Family-scoped only — deliberately NOT visibility-filtered here.
        Detail/update/destroy rely on CanViewExpense/CanEditExpense to
        return a proper 403 for an existing-but-restricted expense,
        rather than a queryset filter silently turning it into a 404.
        List uses get_list_queryset() below, which does apply visibility.
        """
        if getattr(self, "swagger_fake_view", False):
            return Expense.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Expense.objects.none()

        return (
            Expense.objects.filter(family_id=user.family_id, is_deleted=False)
            .select_related("category", "household", "paid_by")
            .prefetch_related("participants", "attachments", "settlements")
        )

    def get_list_queryset(self):
        qs = self.get_queryset()
        user = self.request.user
        if user.role == "family_admin":
            return qs

        member = getattr(user, "member_profile", None)
        if member is None:
            return qs.none()

        visible = Q(visibility="family") | Q(paid_by=member)
        if member.household_id:
            visible |= Q(visibility="household", household_id=member.household_id)
        return qs.filter(visible)

    # Date-range filtering isn't a DjangoFilterBackend field (range needs
    # two params), so it's applied manually here on top of filter_backends.
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        request = self.request
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(expense_date__lte=date_to)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCreateSerializer
        if self.action in ("update", "partial_update"):
            return ExpenseUpdateSerializer
        return ExpenseSerializer

    def get_permissions(self):
        if self.action in ("destroy", "restore"):
            return [permissions.IsAuthenticated(), IsFamilyAdminForDestructive()]
        if self.action in ("update", "partial_update"):
            return [permissions.IsAuthenticated(), CanEditExpense()]
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), CanViewExpense()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        participants = data.pop("participants")
        split_type = data.pop("split_type")

        if split_type == "equal":
            split_data = [str(p["member_id"]) for p in participants]
        else:
            split_data = {str(p["member_id"]): p["value"] for p in participants}

        try:
            expense = expense_service.create_expense(
                actor=request.user,
                family_id=request.user.family_id,
                data=data,
                split_type=split_type,
                split_data=split_data,
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=ExpenseSerializer(self.get_queryset().get(id=expense.id)).data,
            message="Expense created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        expense = self.get_object()
        serializer = self.get_serializer(expense, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            expense = expense_service.update_expense(
                actor=request.user, expense=expense, data=serializer.validated_data
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=ExpenseSerializer(self.get_queryset().get(id=expense.id)).data,
            message="Expense updated",
        )

    def destroy(self, request, *args, **kwargs):
        expense = self.get_object()
        expense_service.cancel_expense(actor=request.user, expense=expense)
        return success_response(message="Expense cancelled")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_list_queryset()))
        return self.get_paginated_response(ExpenseSerializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=ExpenseSerializer(self.get_object()).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsFamilyAdminForDestructive],
    )
    def restore(self, request, pk=None):
        expense = get_object_or_404(Expense, id=pk, family_id=request.user.family_id)
        expense_service.restore_expense(actor=request.user, expense=expense)
        return success_response(data=ExpenseSerializer(expense).data, message="Expense restored")

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def attachments(self, request, pk=None):
        expense = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return error_response("No file provided.", status_code=400)

        attachment = attachment_service.upload_attachment(
            actor=request.user, expense=expense, file_obj=file_obj
        )
        return success_response(
            data=ExpenseAttachmentSerializer(attachment).data,
            message="Attachment uploaded",
            status_code=201,
        )

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        expense = self.get_object()
        return success_response(
            data=ExpenseCommentSerializer(expense.comments.all(), many=True).data
        )

    @action(detail=True, methods=["post"], url_path="comments/add")
    def add_comment(self, request, pk=None):
        expense = self.get_object()
        serializer = ExpenseCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = getattr(request.user, "member_profile", None)
        if member is None:
            return error_response(
                "You don't have a member profile in this family.", status_code=403
            )

        comment = ExpenseComment.objects.create(
            expense=expense, member=member, comment=serializer.validated_data["comment"]
        )
        return success_response(
            data=ExpenseCommentSerializer(comment).data, message="Comment added", status_code=201
        )

    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        expense = self.get_object()
        serializer = RecordSettlementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            settlement = settlement_service.record_settlement(
                actor=request.user, expense=expense, **serializer.validated_data
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=ExpenseSettlementSerializer(settlement).data,
            message="Settlement recorded",
            status_code=201,
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.filter_queryset(self.get_list_queryset())
        by_category = list(
            qs.values("category__name").annotate(total=Sum("amount")).order_by("-total")
        )
        by_household = list(
            qs.values("household__household_name").annotate(total=Sum("amount")).order_by("-total")
        )
        by_member = list(
            qs.values("paid_by__display_name").annotate(total=Sum("amount")).order_by("-total")
        )
        by_status = list(
            qs.values("status").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")
        )
        grand_total = qs.aggregate(total=Sum("amount"))["total"] or 0

        return success_response(
            data={
                "grand_total": str(grand_total),
                "by_category": by_category,
                "by_household": by_household,
                "by_member": by_member,
                "by_status": by_status,
            }
        )

    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_list_queryset())
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Expense Number",
                "Title",
                "Category",
                "Household",
                "Paid By",
                "Amount",
                "Currency",
                "Date",
                "Status",
            ]
        )
        for expense in qs:
            writer.writerow(
                [
                    expense.expense_number,
                    expense.title,
                    expense.category.name if expense.category else "",
                    expense.household.household_name if expense.household else "",
                    expense.paid_by.display_name,
                    expense.amount,
                    expense.currency,
                    expense.expense_date,
                    expense.status,
                ]
            )

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="expenses.csv"'
        return response


class AttachmentDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, attachment_id):
        from .models import ExpenseAttachment

        attachment = get_object_or_404(ExpenseAttachment, id=attachment_id)
        if not CanViewExpense().has_object_permission(request, self, attachment.expense):
            return error_response("You don't have access to this attachment.", status_code=403)

        attachment_service.record_download(actor=request.user, attachment=attachment)
        return success_response(data=ExpenseAttachmentSerializer(attachment).data)
