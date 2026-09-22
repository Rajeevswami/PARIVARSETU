from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.common.crypto import encrypt_json

from .models import ApplicationConfiguration


@receiver(pre_save, sender=ApplicationConfiguration)
def encrypt_provider_secrets(sender, instance, **kwargs):
    instance.email_config = encrypt_json(instance.email_config)
    instance.sms_config = encrypt_json(instance.sms_config)
