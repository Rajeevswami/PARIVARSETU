"""Views stay thin: parse/validate, call FamilyService, shape the response."""

from django.db.models import Count, Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .models import Family
from .permissions import IsFamilyAdminOfObject
from .serializers import FamilyCreateSerializer, FamilySerializer, FamilyUpdateSerializer
from .services import family_service


class FamilyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["family_name", "family_code", "city", "state"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Family.objects.filter(is_deleted=False)
            .annotate(
                member_count=Count("members", filter=Q(members__is_deleted=False), distinct=True),
                household_count=Count(
                    "households", filter=Q(households__is_deleted=False), distinct=True
                ),
            )
            .order_by("-created_at")
        )
        if user.is_staff:
            return qs
        if user.family_id is None:
            return qs.none()
        return qs.filter(id=user.family_id)

    def get_serializer_class(self):
        if self.action == "create":
            return FamilyCreateSerializer
        if self.action in ("update", "partial_update"):
            return FamilyUpdateSerializer
        return FamilySerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            return [permissions.IsAuthenticated(), IsFamilyAdminOfObject()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            family = family_service.create_family(user=request.user, data=serializer.validated_data)
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=FamilySerializer(self.get_queryset().get(id=family.id)).data,
            message="Family created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        family = self.get_object()
        serializer = self.get_serializer(family, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        family = family_service.update_family(
            user=request.user, family=family, data=serializer.validated_data
        )
        return success_response(
            data=FamilySerializer(self.get_queryset().get(id=family.id)).data,
            message="Family updated",
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = FamilySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=FamilySerializer(self.get_object()).data)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        if request.user.family_id is None:
            return error_response("You don't belong to a family yet.", status_code=404)
        family = self.get_queryset().get(id=request.user.family_id)
        return success_response(data=FamilySerializer(family).data)
