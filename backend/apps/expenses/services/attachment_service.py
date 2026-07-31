"""Business logic for expense attachment upload/download tracking."""

from apps.audit import services as audit_services

from ..models import Expense, ExpenseAttachment


def upload_attachment(*, actor, expense: Expense, file_obj) -> ExpenseAttachment:
    checksum = ExpenseAttachment.compute_checksum(file_obj)
    attachment = ExpenseAttachment.objects.create(
        expense=expense,
        file=file_obj,
        file_name=file_obj.name,
        mime_type=getattr(file_obj, "content_type", "") or "",
        file_size=file_obj.size,
        checksum=checksum,
        uploaded_by=actor,
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_ATTACHMENT_UPLOADED,
        target_model="ExpenseAttachment",
        target_id=attachment.id,
        family_id=expense.family_id,
        metadata={"file_name": attachment.file_name},
    )
    return attachment


def record_download(*, actor, attachment: ExpenseAttachment) -> None:
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_ATTACHMENT_DOWNLOADED,
        target_model="ExpenseAttachment",
        target_id=attachment.id,
        family_id=attachment.expense.family_id,
        metadata={"file_name": attachment.file_name},
    )
