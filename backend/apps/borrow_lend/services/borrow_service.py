"""Business logic for BorrowTransaction creation."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.households.models import Household
from apps.loans.models import LedgerPostingEvent
from apps.loans.services import ledger_hook
from apps.members.models import Member

from ..models import BorrowTransaction


def _assert_member_in_family(member: Member, family_id) -> None:
    if member.family_id != family_id:
        raise ApplicationError(
            "Borrower/lender must belong to the same family.",
            code="cross_family_party",
            status_code=403,
        )


def _assert_household_in_family(household: Household | None, family_id) -> None:
    if household is not None and household.family_id != family_id:
        raise ApplicationError(
            "The household must belong to the same family.",
            code="cross_family_household",
            status_code=403,
        )


def create_borrow_transaction(*, actor, family_id, data: dict) -> BorrowTransaction:
    borrower: Member = data["borrower"]
    _assert_member_in_family(borrower, family_id)
    _assert_household_in_family(data.get("household"), family_id)

    lender = data.get("lender")
    if lender is not None:
        _assert_member_in_family(lender, family_id)
        if lender.id == borrower.id:
            raise ApplicationError(
                "Borrower and lender cannot be the same person.", code="same_party"
            )
    elif not data.get("external_lender_name"):
        raise ApplicationError(
            "Provide either an internal lender or an external lender name.", code="lender_required"
        )

    transaction = BorrowTransaction.objects.create(
        family_id=family_id, created_by=actor, updated_by=actor, **data
    )

    ledger_hook.queue_posting(
        family_id=family_id,
        event_type=LedgerPostingEvent.BORROW_ENTRY,
        amount=transaction.amount,
        source_model="BorrowTransaction",
        source_id=transaction.id,
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.BORROW_CREATED,
        target_model="BorrowTransaction",
        target_id=transaction.id,
        family_id=family_id,
        metadata={"amount": str(transaction.amount)},
    )
    return transaction
