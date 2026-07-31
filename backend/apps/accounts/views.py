"""
Views stay thin: parse/validate the request, call a service, shape the
response via apps.common.response. No business logic here.
"""

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from apps.audit.models import AuditLog
from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from . import serializers
from .models import User
from .permissions import IsFamilyAdmin
from .services import auth_service, profile_service, user_management_service


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = auth_service.login(
                identifier=serializer.validated_data["identifier"],
                password=serializer.validated_data["password"],
                request=request,
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        user = result["user"]
        return success_response(
            data={
                "user": serializers.UserProfileSerializer(user).data,
                "tokens": result["tokens"],
            },
            message="Login successful",
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            auth_service.logout(
                user=request.user,
                refresh_token=serializer.validated_data["refresh"],
                request=request,
            )
        except (ApplicationError, TokenError) as exc:
            message = exc.message if isinstance(exc, ApplicationError) else "Invalid token."
            return error_response(message, status_code=400)

        return success_response(message="Logged out successfully")


class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = auth_service.logout_all_devices(user=request.user, request=request)
        return success_response(
            data={"sessions_revoked": count}, message="Logged out from all devices"
        )


@method_decorator(
    ratelimit(key="post:identifier", rate="5/h", method="POST", block=True), name="post"
)
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_service.forgot_password(
            identifier=serializer.validated_data["identifier"], request=request
        )
        # Same response regardless of whether the identifier matched a user.
        return success_response(
            message="If an account exists for that email/mobile, a reset link has been sent."
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            auth_service.reset_password(
                token=serializer.validated_data["token"],
                new_password=serializer.validated_data["new_password"],
                request=request,
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(message="Password reset successfully")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            auth_service.change_password(
                user=request.user,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
                request=request,
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)

        return success_response(message="Password changed successfully")


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data=serializers.UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = serializers.ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        user = profile_service.update_profile(
            user=request.user, data=serializer.validated_data, request=request
        )
        return success_response(
            data=serializers.UserProfileSerializer(user).data, message="Profile updated"
        )


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = serializers.AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = profile_service.upload_avatar(
            user=request.user,
            photo_file=serializer.validated_data["profile_photo"],
            request=request,
        )
        return success_response(
            data=serializers.UserProfileSerializer(user).data, message="Avatar updated"
        )


class LoginHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LoginHistorySerializer

    def get_queryset(self):
        return AuditLog.objects.filter(
            actor=self.request.user,
            action__in=["login", "login_failed", "logout", "logout_all"],
        )


class MemberResetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def post(self, request, member_id):
        member = generics.get_object_or_404(User, id=member_id)
        try:
            temp_password = user_management_service.reset_member_password(
                admin=request.user, member=member
            )
        except ApplicationError as exc:
            return error_response(exc.message, status_code=exc.status_code)

        return success_response(
            data={"temporary_password": temp_password},
            message="Member password reset. Share the temporary password securely.",
        )


class MemberDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def post(self, request, member_id):
        member = generics.get_object_or_404(User, id=member_id)
        try:
            user_management_service.deactivate_member(admin=request.user, member=member)
        except ApplicationError as exc:
            return error_response(exc.message, status_code=exc.status_code)

        return success_response(message="Member deactivated")


class MemberReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def post(self, request, member_id):
        member = generics.get_object_or_404(User, id=member_id)
        try:
            user_management_service.reactivate_member(admin=request.user, member=member)
        except ApplicationError as exc:
            return error_response(exc.message, status_code=exc.status_code)

        return success_response(message="Member reactivated")
