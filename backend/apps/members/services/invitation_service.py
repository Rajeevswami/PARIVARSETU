"""
Invitation lifecycle: send, accept (creating the invitee's account inline
if they don't have one yet — there is no separate public registration
endpoint, this is the intended entry point), and reject.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import InvitationStatus, Member, MemberInvitation

User = get_user_model()

INVITATION_EXPIRY_DAYS = 7


def send_invitation(*, admin, data: dict) -> MemberInvitation:
    email = data.get("email")
    mobile = data.get("mobile")

    if not email and not mobile:
        raise ApplicationError(
            "Provide an email or a mobile number to invite.", code="missing_identifier"
        )

    lookup = Q()
    if email:
        lookup |= Q(email__iexact=email)
    if mobile:
        lookup |= Q(mobile=mobile)
    existing_user = User.objects.filter(lookup).first() if lookup else None
    if existing_user and existing_user.family_id is not None:
        raise ApplicationError("This person already belongs to a family.", code="already_in_family")

    household = data.pop("household", None)
    if household is not None and household.family_id != admin.family_id:
        raise ApplicationError(
            "The household must belong to your family.", code="cross_family_action", status_code=403
        )

    invitation = MemberInvitation.objects.create(
        family_id=admin.family_id,
        household=household,
        invited_by=admin,
        token=secrets.token_urlsafe(24),
        expires_at=timezone.now() + timedelta(days=INVITATION_EXPIRY_DAYS),
        **data,
    )

    # Email delivery reuses the same architecture as the accounts module —
    # console backend for now, Celery task for the real send.
    from apps.accounts.tasks import send_invitation_email_task

    invite_link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"
    send_invitation_email_task.delay(str(invitation.id), invite_link)

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.INVITATION_SENT,
        target_model="MemberInvitation",
        target_id=invitation.id,
        family_id=admin.family_id,
        metadata={"email": email, "mobile": mobile},
    )
    return invitation


def accept_invitation(*, token: str, accept_data: dict, request=None) -> Member:
    invitation = (
        MemberInvitation.objects.filter(token=token).select_related("family", "household").first()
    )
    if invitation is None or not invitation.is_valid:
        raise ApplicationError(
            "This invitation is invalid or has expired.", code="invalid_invitation"
        )

    user = None
    if invitation.email:
        user = User.objects.filter(email__iexact=invitation.email).first()
    if user is None and invitation.mobile:
        user = User.objects.filter(mobile=invitation.mobile).first()

    if user is None:
        # Brand-new invitee — create their account as part of accepting.
        password = accept_data.get("password")
        first_name = accept_data.get("first_name")
        if not password or not first_name:
            raise ApplicationError(
                "first_name and password are required to accept this invitation.",
                code="account_details_required",
            )
        user = User.objects.create_user(
            email=invitation.email or f"{invitation.mobile}@placeholder.parivarsetu.app",
            password=password,
            first_name=first_name,
            mobile=invitation.mobile,
            is_verified=True,
        )
    elif user.family_id is not None:
        raise ApplicationError(
            "This account already belongs to a family.", code="already_in_family"
        )

    from apps.accounts.models import UserRole, UserStatus

    user.family = invitation.family
    user.household = invitation.household
    user.role = invitation.role if invitation.role in UserRole.values else UserRole.MEMBER
    user.status = UserStatus.ACTIVE
    user.save(update_fields=["family", "household", "role", "status"])

    member = Member.objects.create(
        user=user,
        family=invitation.family,
        household=invitation.household,
        display_name=user.get_full_name() or user.email,
        relationship=invitation.relationship,
        created_by=invitation.invited_by,
        updated_by=invitation.invited_by,
    )

    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["status", "accepted_at"])

    audit_services.record(
        actor=user,
        action=audit_services.AuditAction.INVITATION_ACCEPTED,
        target_model="MemberInvitation",
        target_id=invitation.id,
        family_id=invitation.family_id,
    )
    return member


def reject_invitation(*, token: str) -> MemberInvitation:
    invitation = MemberInvitation.objects.filter(token=token).first()
    if invitation is None or not invitation.is_valid:
        raise ApplicationError(
            "This invitation is invalid or has expired.", code="invalid_invitation"
        )

    invitation.status = InvitationStatus.REJECTED
    invitation.rejected_at = timezone.now()
    invitation.save(update_fields=["status", "rejected_at"])

    audit_services.record(
        action=audit_services.AuditAction.INVITATION_REJECTED,
        target_model="MemberInvitation",
        target_id=invitation.id,
        family_id=invitation.family_id,
    )
    return invitation
