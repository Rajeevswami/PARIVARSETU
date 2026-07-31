"""
Business logic for Reminder create/dismiss. Data records only — no
delivery. A future Notifications module reads pending reminders and
actually sends them.
"""

from apps.audit import services as audit_services

from ..models import Reminder, ReminderStatus


def create_reminder(*, actor, family_id, data: dict) -> Reminder:
    reminder = Reminder.objects.create(family_id=family_id, created_by=actor, **data)

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_REMINDER_CREATED,
        target_model="Reminder",
        target_id=reminder.id,
        family_id=family_id,
        metadata={"reminder_type": reminder.reminder_type},
    )
    return reminder


def dismiss_reminder(*, actor, reminder: Reminder) -> Reminder:
    reminder.status = ReminderStatus.DISMISSED
    reminder.save(update_fields=["status"])

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_REMINDER_DISMISSED,
        target_model="Reminder",
        target_id=reminder.id,
        family_id=reminder.family_id,
    )
    return reminder
