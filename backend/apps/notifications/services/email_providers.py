"""Transactional email. SendGrid is called directly; SES uses the configured Django backend."""

import json
import logging
import urllib.request

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger("apps.errors")


def send_transactional(*, to_email: str, subject: str, text: str, html: str = "") -> None:
    provider = getattr(settings, "EMAIL_PROVIDER", "console")
    if provider == "sendgrid" and settings.SENDGRID_API_KEY:
        _sendgrid(to_email=to_email, subject=subject, text=text, html=html)
        return
    message = EmailMultiAlternatives(
        subject=subject, body=text, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email]
    )
    if html:
        message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)


def _sendgrid(*, to_email: str, subject: str, text: str, html: str) -> None:
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {
            "email": settings.DEFAULT_FROM_EMAIL.split("<")[-1].strip(" >"),
            "name": settings.PRODUCT_NAME,
        },
        "subject": subject,
        "content": [{"type": "text/plain", "value": text}],
    }
    if html:
        payload["content"].append({"type": "text/html", "value": html})
    request = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status >= 300:
            logger.error("SendGrid rejected a message to %s", to_email)
