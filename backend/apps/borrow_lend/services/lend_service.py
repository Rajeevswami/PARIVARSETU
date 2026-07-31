"""Business logic for LendTransaction creation."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.households.models import Household
from apps.loans.models import LedgerPostingEvent
from apps.loans.services import ledger_hook
from apps.members.models import Member

from ..models import LendTransaction


def _assert_member_in_family(member: Member, family_id) -> None:
    if member.family_id != family_id:
        raise ApplicationError(
            "Giver/receiver must belong to the same family.",
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


def create_lend_transaction(*, actor, family_id, data: dict) -> LendTransaction:
    giver: Member = data["giver"]
    _assert_member_in_family(giver, family_id)
    _assert_household_in_family(data.get("household"), family_id)

    receiver = data.get("receiver")
    if receiver is not None:
        _assert_member_in_family(receiver, family_id)
        if receiver.id == giver.id:
            raise ApplicationError(
                "Giver and receiver cannot be the same person.", code="same_party"
            )
    elif not data.get("external_receiver_name"):
        raise ApplicationError(
            "Provide either an internal receiver or an external receiver name.",
            code="receiver_required",
        )

    transaction = LendTransaction.objects.create(
        family_id=family_id, created_by=actor, updated_by=actor, **data
    )

    ledger_hook.queue_posting(
        family_id=family_id,
        event_type=LedgerPostingEvent.LEND_ENTRY,
        amount=transaction.amount,
        source_model="LendTransaction",
        source_id=transaction.id,
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LEND_CREATED,
        target_model="LendTransaction",
        target_id=transaction.id,
        family_id=family_id,
        metadata={"amount": str(transaction.amount)},
    )
    return transaction
