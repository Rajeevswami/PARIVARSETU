"""Celery wrappers around email_service — the async entry points callers use."""

from celery import shared_task

from .services import email_service


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(self, user_id, reset_link: str):
    from .models import User

    try:
        user = User.objects.get(id=user_id)
        email_service.send_password_reset_email(user=user, reset_link=reset_link)
    except Exception as exc:  # noqa: BLE001 — retry on any transient send failure
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_id):
    from .models import User

    try:
        user = User.objects.get(id=user_id)
        email_service.send_welcome_email(user=user)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invitation_email_task(self, invitation_id, invite_link: str):
    from apps.members.models import MemberInvitation

    try:
        invitation = MemberInvitation.objects.select_related("family", "invited_by").get(
            id=invitation_id
        )
        if not invitation.email:
            return  # mobile-only invitations aren't emailed
        email_service.send_invitation_email(
            to_email=invitation.email,
            invited_by_name=invitation.invited_by.get_full_name() or invitation.invited_by.email,
            family_name=invitation.family.family_name,
            invite_link=invite_link,
        )
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)
