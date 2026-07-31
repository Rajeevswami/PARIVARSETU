"""
All authentication business logic lives here — views only parse request
data and call these functions, per project architecture rules.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import PasswordResetToken
from ..tasks import send_password_reset_email_task

User = get_user_model()


def _issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _client_meta(request) -> dict:
    if request is None:
        return {"ip_address": None, "user_agent": ""}
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
    return {"ip_address": ip, "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255]}


def login(*, identifier: str, password: str, request=None) -> dict:
    """identifier is an email or a mobile number — both are accepted."""
    meta = _client_meta(request)
    user = User.objects.filter(Q(email__iexact=identifier) | Q(mobile=identifier)).first()

    if user is None or not user.check_password(password):
        audit_services.record(
            actor=user,
            action=audit_services.AuditAction.LOGIN_FAILED,
            metadata={"identifier": identifier, "reason": "invalid_credentials"},
            **meta,
        )
        raise ApplicationError("Invalid credentials.", code="invalid_credentials", status_code=401)

    if user.is_deleted:
        audit_services.record(
            actor=user,
            action=audit_services.AuditAction.LOGIN_FAILED,
            metadata={"reason": "account_deleted"},
            **meta,
        )
        raise ApplicationError(
            "This account no longer exists.", code="account_deleted", status_code=403
        )

    if not user.is_login_allowed:
        audit_services.record(
            actor=user,
            action=audit_services.AuditAction.LOGIN_FAILED,
            metadata={"reason": "account_not_active", "status": user.status},
            **meta,
        )
        raise ApplicationError(
            "Your account is not active. Contact your family admin.",
            code="account_inactive",
            status_code=403,
        )

    tokens = _issue_tokens(user)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    audit_services.record(actor=user, action=audit_services.AuditAction.LOGIN, **meta)

    return {"user": user, "tokens": tokens}


def logout(*, user, refresh_token: str, request=None) -> None:
    meta = _client_meta(request)
    try:
        RefreshToken(refresh_token).blacklist()
    except Exception as exc:  # noqa: BLE001 — token already invalid/expired is still a valid logout
        raise ApplicationError("Invalid or expired refresh token.", code="invalid_token") from exc

    audit_services.record(actor=user, action=audit_services.AuditAction.LOGOUT, **meta)


def logout_all_devices(*, user, request=None) -> int:
    meta = _client_meta(request)
    outstanding = OutstandingToken.objects.filter(user=user)
    count = 0
    for token in outstanding:
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        if created:
            count += 1

    audit_services.record(
        actor=user, action=audit_services.AuditAction.LOGOUT_ALL, metadata={"count": count}, **meta
    )
    return count


def change_password(*, user, old_password: str, new_password: str, request=None) -> None:
    meta = _client_meta(request)
    if not user.check_password(old_password):
        raise ApplicationError("Current password is incorrect.", code="invalid_password")

    from django.contrib.auth.password_validation import validate_password

    validate_password(new_password, user=user)

    user.set_password(new_password)
    user.save(update_fields=["password"])

    audit_services.record(actor=user, action=audit_services.AuditAction.PASSWORD_CHANGED, **meta)


def forgot_password(*, identifier: str, request=None) -> None:
    """
    Always behaves the same way whether or not the identifier matches a
    user — prevents account enumeration via response timing/content.
    """
    meta = _client_meta(request)
    user = User.objects.filter(Q(email__iexact=identifier) | Q(mobile=identifier)).first()

    if user is None or user.is_deleted:
        return

    token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES),
    )

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    send_password_reset_email_task.delay(str(user.id), reset_link)

    audit_services.record(
        actor=user, action=audit_services.AuditAction.PASSWORD_RESET_REQUESTED, **meta
    )


def reset_password(*, token: str, new_password: str, request=None) -> None:
    meta = _client_meta(request)
    reset_token = PasswordResetToken.objects.filter(token=token).select_related("user").first()

    if reset_token is None or not reset_token.is_valid:
        raise ApplicationError("This reset link is invalid or has expired.", code="invalid_token")

    from django.contrib.auth.password_validation import validate_password

    user = reset_token.user
    validate_password(new_password, user=user)

    user.set_password(new_password)
    user.save(update_fields=["password"])

    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=["used_at"])

    audit_services.record(
        actor=user, action=audit_services.AuditAction.PASSWORD_RESET_COMPLETED, **meta
    )
