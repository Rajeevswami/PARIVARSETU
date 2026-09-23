"""
Signal-driven side effects for the accounts app.

Kept intentionally minimal — anything with real business logic (audit
writes, permission checks) lives in services/ and is called directly from
views, not fired implicitly from signals, so it stays easy to trace.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .services import email_service
from .tasks import deliver, send_welcome_email_task


@receiver(post_save, sender=User)
def send_welcome_email_on_creation(sender, instance: User, created: bool, **kwargs):
    if created and instance.email and not settings.TESTING:
        deliver(
            send_welcome_email_task,
            (str(instance.id),),
            lambda: email_service.send_welcome_email(user=instance),
        )
