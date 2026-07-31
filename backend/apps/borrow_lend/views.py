"""Views stay thin: parse/validate, call the appropriate service, shape the response."""

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .models import BorrowTransaction, LendTransaction
from .permissions import CanViewBorrow, CanViewLend
from .serializers import (
    BorrowTransactionCreateSerializer,
    BorrowTransactionSerializer,
    LendTransactionCreateSerializer,
    LendTransactionSerializer,
    RecordSettlementSerializer,
    SettlementSerializer,
)
from .services import borrow_service, lend_service, settlement_service


class BorrowTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "household", "borrower", "payment_method"]
    search_fields = ["transaction_number", "borrower__display_name", "lender__display_name"]
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BorrowTransaction.objects.none()
        user = self.request.user
        if user.family_id is None:
            return BorrowTransaction.objects.none()
        return BorrowTransaction.objects.filter(
            family_id=user.family_id, is_deleted=False
        ).select_related("borrower", "lender", "household")

    def get_list_queryset(self):
        qs = self.get_queryset()
        user = self.request.user
        if user.role == "family_admin":
            return qs
        member = getattr(user, "member_profile", None)
        if member is None:
            return qs.none()
        return qs.filter(Q(borrower=member) | Q(lender=member))

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowTransactionCreateSerializer
        return BorrowTransactionSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), CanViewBorrow()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transaction = borrow_service.create_borrow_transaction(
                actor=request.user,
                family_id=request.user.family_id,
                data=dict(serializer.validated_data),
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=BorrowTransactionSerializer(self.get_queryset().get(id=transaction.id)).data,
            message="Borrow transaction created",
            status_code=201,
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_list_queryset()))
        return self.get_paginated_response(BorrowTransactionSerializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=BorrowTransactionSerializer(self.get_object()).data)


class LendTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "household", "giver", "payment_method"]
    search_fields = ["transaction_number", "giver__display_name", "receiver__display_name"]
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LendTransaction.objects.none()
        user = self.request.user
        if user.family_id is None:
            return LendTransaction.objects.none()
        return LendTransaction.objects.filter(
            family_id=user.family_id, is_deleted=False
        ).select_related("giver", "receiver", "household")

    def get_list_queryset(self):
        qs = self.get_queryset()
        user = self.request.user
        if user.role == "family_admin":
            return qs
        member = getattr(user, "member_profile", None)
        if member is None:
            return qs.none()
        return qs.filter(Q(giver=member) | Q(receiver=member))

    def get_serializer_class(self):
        if self.action == "create":
            return LendTransactionCreateSerializer
        return LendTransactionSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), CanViewLend()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transaction = lend_service.create_lend_transaction(
                actor=request.user,
                family_id=request.user.family_id,
                data=dict(serializer.validated_data),
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=LendTransactionSerializer(self.get_queryset().get(id=transaction.id)).data,
            message="Lend transaction created",
            status_code=201,
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_list_queryset()))
        return self.get_paginated_response(LendTransactionSerializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=LendTransactionSerializer(self.get_object()).data)


class SettlementView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecordSettlementSerializer

    def post(self, request):
        serializer = RecordSettlementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            settlement = settlement_service.record_settlement(
                actor=request.user, **serializer.validated_data
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=SettlementSerializer(settlement).data,
            message="Settlement recorded",
            status_code=201,
        )
