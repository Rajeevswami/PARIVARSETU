"""
Generic audit trail — one model, reused by every module. This module's
authentication system uses it to record login, logout, password change,
profile update, and failed login events; later modules log their own
create/update/delete events into the same table.
"""

import uuid

from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    LOGIN = "login", "Login"
    LOGIN_FAILED = "login_failed", "Login Failed"
    LOGOUT = "logout", "Logout"
    LOGOUT_ALL = "logout_all", "Logout All Devices"
    PASSWORD_CHANGED = "password_changed", "Password Changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password Reset Requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed", "Password Reset Completed"
    PROFILE_UPDATED = "profile_updated", "Profile Updated"
    AVATAR_UPDATED = "avatar_updated", "Avatar Updated"
    MEMBER_DEACTIVATED = "member_deactivated", "Member Deactivated"
    MEMBER_REACTIVATED = "member_reactivated", "Member Reactivated"
    MEMBER_PASSWORD_RESET = "member_password_reset", "Member Password Reset by Admin"

    FAMILY_CREATED = "family_created", "Family Created"
    FAMILY_UPDATED = "family_updated", "Family Updated"
    HOUSEHOLD_CREATED = "household_created", "Household Created"
    HOUSEHOLD_UPDATED = "household_updated", "Household Updated"
    HOUSEHOLD_DEACTIVATED = "household_deactivated", "Household Deactivated"
    HOUSEHOLD_HEAD_CHANGED = "household_head_changed", "Household Head Changed"
    MEMBER_PROFILE_CREATED = "member_profile_created", "Member Profile Created"
    MEMBER_PROFILE_UPDATED = "member_profile_updated", "Member Profile Updated"
    MEMBER_TRANSFERRED = "member_transferred", "Member Transferred"
    INVITATION_SENT = "invitation_sent", "Invitation Sent"
    INVITATION_ACCEPTED = "invitation_accepted", "Invitation Accepted"
    INVITATION_REJECTED = "invitation_rejected", "Invitation Rejected"

    EXPENSE_CREATED = "expense_created", "Expense Created"
    EXPENSE_UPDATED = "expense_updated", "Expense Updated"
    EXPENSE_CANCELLED = "expense_cancelled", "Expense Cancelled"
    EXPENSE_RESTORED = "expense_restored", "Expense Restored"
    EXPENSE_CATEGORY_CREATED = "expense_category_created", "Expense Category Created"
    EXPENSE_CATEGORY_UPDATED = "expense_category_updated", "Expense Category Updated"
    EXPENSE_SETTLEMENT_RECORDED = "expense_settlement_recorded", "Expense Settlement Recorded"
    EXPENSE_ATTACHMENT_UPLOADED = "expense_attachment_uploaded", "Expense Attachment Uploaded"
    EXPENSE_ATTACHMENT_DOWNLOADED = "expense_attachment_downloaded", "Expense Attachment Downloaded"

    LOAN_CREATED = "loan_created", "Loan Created"
    LOAN_UPDATED = "loan_updated", "Loan Updated"
    LOAN_CANCELLED = "loan_cancelled", "Loan Cancelled"
    LOAN_RESTORED = "loan_restored", "Loan Restored"
    LOAN_PAYMENT_ADDED = "loan_payment_added", "Loan Payment Added"
    LOAN_REMINDER_CREATED = "loan_reminder_created", "Loan Reminder Created"
    LOAN_REMINDER_DISMISSED = "loan_reminder_dismissed", "Loan Reminder Dismissed"
    LOAN_DOCUMENT_UPLOADED = "loan_document_uploaded", "Loan Document Uploaded"
    BORROW_CREATED = "borrow_created", "Borrow Transaction Created"
    LEND_CREATED = "lend_created", "Lend Transaction Created"
    BORROW_LEND_SETTLEMENT_RECORDED = (
        "borrow_lend_settlement_recorded",
        "Borrow/Lend Settlement Recorded",
    )

    LEDGER_ACCOUNT_CREATED = "ledger_account_created", "Ledger Account Created"
    LEDGER_JOURNAL_CREATED = "ledger_journal_created", "Journal Created"
    LEDGER_JOURNAL_POSTED = "ledger_journal_posted", "Journal Posted"
    LEDGER_ADJUSTMENT_CREATED = "ledger_adjustment_created", "Adjustment Entry Created"
    LEDGER_STATEMENT_EXPORTED = "ledger_statement_exported", "Statement Exported"
    LEDGER_BALANCE_UPDATED = "ledger_balance_updated", "Account Balance Updated"
    LEDGER_PERIOD_CLOSED = "ledger_period_closed", "Financial Period Closed"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        help_text="Who performed the action. Null for unauthenticated events (e.g. failed login).",
    )
    action = models.CharField(max_length=40, choices=AuditAction.choices, db_index=True)

    # What the action was performed on — generic so any module can log
    # against any of its own models without a hard FK dependency here.
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)

    family_id = models.UUIDField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} by {self.actor_id} at {self.created_at:%Y-%m-%d %H:%M}"
import uuid
from django.db import models
class AuditFieldChange(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); audit_log=models.ForeignKey("audit.AuditLog",on_delete=models.CASCADE,related_name="field_changes"); field_name=models.CharField(max_length=100); old_value=models.JSONField(null=True,blank=True); new_value=models.JSONField(null=True,blank=True)
 class Meta: db_table="audit_field_change"; indexes=[models.Index(fields=["audit_log","field_name"])]
