"""Stamp family_id onto child rows and reject a parent from another family."""

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver


def _require_same_family(child_family_id, parent_family_id, message: str) -> None:
    if parent_family_id is None or child_family_id != parent_family_id:
        raise ValidationError(message)


@receiver(pre_save)
def stamp_family_scope(sender, instance, **kwargs):
    if sender.__module__ == "__fake__":
        return
    label = instance._meta.label
    if label == "assistant.Message":
        instance.family_id = instance.conversation.family_id
    elif label == "assistant.ChannelLink":
        instance.family_id = instance.user.family_id
        if instance.family_id is None:
            raise ValidationError("A channel link requires a user who belongs to a family.")
    elif label == "borrow_lend.Settlement":
        from apps.borrow_lend.models import BorrowTransaction, LendTransaction

        model = BorrowTransaction if instance.reference_type == "borrow" else LendTransaction
        parent_family_id = (
            model.objects.filter(id=instance.reference_id)
            .values_list("family_id", flat=True)
            .first()
        )
        member_family_id = instance.member.family_id
        _require_same_family(
            member_family_id,
            parent_family_id,
            "Settlement member must belong to the same family as the transaction.",
        )
        instance.family_id = parent_family_id
    elif label == "documents.DocumentShare":
        instance.family_id = instance.document.family_id
        _require_same_family(
            instance.shared_with.family_id,
            instance.family_id,
            "A document can only be shared with a member of the same family.",
        )
    elif label == "documents.DocumentAccessLog":
        instance.family_id = instance.document.family_id
        if instance.member_id and instance.member.family_id != instance.family_id:
            raise ValidationError("Access log member must belong to the document family.")
    elif label == "ledger.LedgerEntry":
        instance.family_id = instance.journal.family_id
        _require_same_family(
            instance.ledger_account.family_id,
            instance.family_id,
            "Ledger entry account must belong to the journal family.",
        )
    elif label == "ledger.AccountBalance":
        instance.family_id = instance.account.family_id
    elif label == "loans.LoanInstallment":
        instance.family_id = instance.loan.family_id
    elif label == "loans.LoanPayment":
        instance.family_id = instance.loan.family_id
    elif label == "notifications.LoginHistory":
        instance.family_id = instance.member.family_id
    elif label == "notifications.SecurityEvent":
        if instance.member_id:
            instance.family_id = instance.member.family_id
        if instance.family_id is None:
            raise ValidationError("A security event must be scoped to a family.")
