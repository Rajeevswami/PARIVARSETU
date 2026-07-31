"""Views stay thin: parse/validate, call the appropriate service, shape the response."""

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsFamilyAdmin
from apps.common.response import error_response, success_response
from apps.households.models import Household

from .models import Member, MemberInvitation
from .permissions import IsSelfOrFamilyAdminMember
from .serializers import (
    AcceptInvitationSerializer,
    MemberCreateSerializer,
    MemberInvitationCreateSerializer,
    MemberInvitationSerializer,
    MemberSerializer,
    MemberUpdateSerializer,
    RejectInvitationSerializer,
    TransferMemberSerializer,
)
from .services import invitation_service, member_service

User = get_user_model()


class MemberViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["household", "status", "gender", "relationship"]
    search_fields = ["display_name", "user__email", "user__mobile", "relationship"]
    ordering_fields = ["created_at", "display_name"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Member.objects.none()
        user = self.request.user
        if user.family_id is None:
            return Member.objects.none()
        return Member.objects.filter(family_id=user.family_id, is_deleted=False).select_related(
            "user", "household"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return MemberCreateSerializer
        if self.action in ("update", "partial_update"):
            return MemberUpdateSerializer
        return MemberSerializer

    def get_permissions(self):
        if self.action in ("create", "transfer"):
            return [permissions.IsAuthenticated(), IsFamilyAdmin()]
        if self.action in ("update", "partial_update", "retrieve"):
            return [permissions.IsAuthenticated(), IsSelfOrFamilyAdminMember()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        target_user = get_object_or_404(User, id=data.pop("user_id"))
        household_id = data.pop("household_id", None)
        household = get_object_or_404(Household, id=household_id) if household_id else None
        data["household"] = household

        try:
            member = member_service.create_member_for_existing_user(
                admin=request.user, target_user=target_user, data=data
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=MemberSerializer(self.get_queryset().get(id=member.id)).data,
            message="Member created",
            status_code=201,
        )

    def partial_update(self, request, *args, **kwargs):
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        member = member_service.update_member(
            actor=request.user, member=member, data=serializer.validated_data
        )
        return success_response(
            data=MemberSerializer(self.get_queryset().get(id=member.id)).data,
            message="Member updated",
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = MemberSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=MemberSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        member = self.get_object()
        serializer = TransferMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        household_id = serializer.validated_data["household_id"]
        new_household = get_object_or_404(Household, id=household_id) if household_id else None

        try:
            member = member_service.transfer_member(
                admin=request.user, member=member, new_household=new_household
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=MemberSerializer(self.get_queryset().get(id=member.id)).data,
            message="Member transferred",
        )


class InvitationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsFamilyAdmin]
    serializer_class = MemberInvitationSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return MemberInvitation.objects.none()
        user = self.request.user
        if user.family_id is None:
            return MemberInvitation.objects.none()
        return MemberInvitation.objects.filter(family_id=user.family_id).select_related("household")

    def create(self, request, *args, **kwargs):
        serializer = MemberInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        try:
            invitation = invitation_service.send_invitation(admin=request.user, data=data)
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=MemberInvitationSerializer(invitation).data,
            message="Invitation sent",
            status_code=201,
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class AcceptInvitationView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AcceptInvitationSerializer

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        token = data.pop("token")

        try:
            member = invitation_service.accept_invitation(
                token=token, accept_data=data, request=request
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(
            data=MemberSerializer(member).data,
            message="Invitation accepted",
            status_code=status.HTTP_200_OK,
        )


class RejectInvitationView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RejectInvitationSerializer

    def post(self, request):
        serializer = RejectInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invitation_service.reject_invitation(token=serializer.validated_data["token"])
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(message="Invitation rejected")
