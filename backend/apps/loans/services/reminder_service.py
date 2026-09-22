"""
Business logic for Reminder create/dismiss. Data records only — no
delivery. A future Notifications module reads pending reminders and
actually sends them.
"""

from apps.audit import services as audit_services

from ..models import Reminder, ReminderStatus


def create_reminder(*, actor, family_id, data: dict) -> Reminder:
    from apps.common.exceptions import ApplicationError

    loan = data.get("loan")
    installment = data.get("installment")
    member = data.get("member")
    if loan is not None and loan.family_id != family_id:
        raise ApplicationError(
            "Loan is outside this family.", code="cross_family_action", status_code=403
        )
    if installment is not None and installment.family_id != family_id:
        raise ApplicationError(
            "Installment is outside this family.", code="cross_family_action", status_code=403
        )
    if member is None or member.family_id != family_id:
        raise ApplicationError(
            "Member is outside this family.", code="cross_family_action", status_code=403
        )
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
