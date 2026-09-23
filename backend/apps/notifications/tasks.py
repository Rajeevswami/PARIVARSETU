from celery import shared_task

from .services.email_providers import send_transactional


@shared_task
def send_transactional_email_task(to_email: str, subject: str, text: str, html: str = "") -> None:
    send_transactional(to_email=to_email, subject=subject, text=text, html=html)
