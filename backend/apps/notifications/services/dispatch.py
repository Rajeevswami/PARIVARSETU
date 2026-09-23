"""In-app notification plus optional email. Business callers use this, not the model."""

from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationPreference

from .email_providers import send_transactional


def notify(
    *, family, recipient, title: str, message: str, notification_type: str, email: bool = False
) -> Notification:
    item = Notification.objects.create(
        family=family,
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    if email and _email_allowed(recipient):
        send_transactional(to_email=recipient.email, subject=title, text=message)
    return item


def notify_family_admins(*, family, title: str, message: str, notification_type: str) -> int:
    users = get_user_model().objects.filter(family=family, role="family_admin", is_active=True)
    count = 0
    for user in users:
        notify(
            family=family,
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            email=True,
        )
        count += 1
    return count


def _email_allowed(user) -> bool:
    preference = NotificationPreference.objects.filter(user=user).first()
    if preference is None:
        return False
    return preference.email_enabled and preference.in_app_enabled
