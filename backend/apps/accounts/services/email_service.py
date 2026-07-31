"""
Email-sending architecture for the accounts app.

Uses Django's console backend by default (see EMAIL_BACKEND in settings) —
no third-party provider is configured yet, per this module's scope. When
one is chosen (SES, SendGrid, Postmark, ...), only EMAIL_BACKEND and its
credentials change; nothing here does.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("apps.errors")


def _send(*, to_email: str, subject: str, template_base: str, context: dict) -> None:
    text_body = render_to_string(f"emails/{template_base}.txt", context)
    html_body = render_to_string(f"emails/{template_base}.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send email (%s) to %s", template_base, to_email)
        raise


def send_password_reset_email(*, user, reset_link: str) -> None:
    _send(
        to_email=user.email,
        subject="Reset your ParivarSetu password",
        template_base="password_reset",
        context={
            "first_name": user.first_name,
            "reset_link": reset_link,
            "expiry_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
        },
    )


def send_welcome_email(*, user) -> None:
    _send(
        to_email=user.email,
        subject="Welcome to ParivarSetu",
        template_base="welcome",
        context={"first_name": user.first_name, "login_link": settings.FRONTEND_URL},
    )


def send_invitation_email(
    *, to_email: str, invited_by_name: str, family_name: str, invite_link: str
) -> None:
    _send(
        to_email=to_email,
        subject=f"{invited_by_name} invited you to join {family_name} on ParivarSetu",
        template_base="invitation",
        context={
            "invited_by_name": invited_by_name,
            "family_name": family_name,
            "invite_link": invite_link,
        },
    )
