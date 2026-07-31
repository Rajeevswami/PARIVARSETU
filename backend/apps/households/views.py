"""Views stay thin: parse/validate, call HouseholdService, shape the response."""

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404

from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsFamilyAdmin, IsFamilyMember
from apps.common.response import error_response, success_response
from apps.members.models import Member

from .models import Household
from .serializers import (
    ChangeHeadSerializer,
    HouseholdCreateSerializer,
    HouseholdSerializer,
    HouseholdUpdateSerializer,
)
from .services import household_service


class HouseholdViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status"]
    search_fields = ["household_name", "household_code", "address"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Household.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Household.objects.none()
        return (
            Household.objects.filter(family_id=user.family_id, is_deleted=False)
            .select_related("head_of_household")
            .annotate(
                member_count=Count("members", filter=Q(members__is_deleted=False), distinct=True)
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return HouseholdCreateSerializer
        if self.action in ("update", "partial_update"):
            return HouseholdUpdateSerializer
        return HouseholdSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "change_head"):
            return [permissions.IsAuthenticated(), IsFamilyAdmin()]
        return [permissions.IsAuthenticated(), IsFamilyMember()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        household = household_service.create_household(
            admin=request.user, data=serializer.validated_data
        )
        return success_response(
            data=HouseholdSerializer(self.get_queryset().get(id=household.id)).data,
            message="Household created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        household = self.get_object()
        serializer = self.get_serializer(household, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        household = household_service.update_household(
            admin=request.user, household=household, data=serializer.validated_data
        )
        return success_response(
            data=HouseholdSerializer(self.get_queryset().get(id=household.id)).data,
            message="Household updated",
        )

    def destroy(self, request, *args, **kwargs):
        household = self.get_object()
        household_service.deactivate_household(admin=request.user, household=household)
        return success_response(message="Household deactivated")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = HouseholdSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=HouseholdSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def change_head(self, request, pk=None):
        household = self.get_object()
        serializer = ChangeHeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = get_object_or_404(Member, id=serializer.validated_data["member_id"])
        try:
            household = household_service.change_head(
                admin=request.user, household=household, member=member
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=HouseholdSerializer(self.get_queryset().get(id=household.id)).data,
            message="Household head updated",
        )
