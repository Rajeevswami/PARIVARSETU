from celery import shared_task

from ai_services.proactive import build_weekly_summary
from apps.families.models import Family
from apps.notifications.services.dispatch import notify_family_admins


@shared_task
def send_weekly_family_summaries() -> int:
    sent = 0
    for family in Family.objects.filter(is_deleted=False, status="active"):
        notify_family_admins(
            family=family,
            title="Weekly family summary",
            message=build_weekly_summary(family),
            notification_type="report",
        )
        sent += 1
    return sent
