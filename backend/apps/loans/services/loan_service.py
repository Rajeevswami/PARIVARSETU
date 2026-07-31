"""Business logic for Loan CRUD and interest calculation."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.households.models import Household
from apps.members.models import Member

from ..models import LedgerPostingEvent, Loan, LoanSource, LoanStatus
from . import ledger_hook
from .interest import calculate_interest


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
            "The household must belong to the same family as the loan.",
            code="cross_family_household",
            status_code=403,
        )


def create_loan(*, actor, family_id, data: dict) -> Loan:
    borrower: Member = data["borrower"]
    _assert_member_in_family(borrower, family_id)
    _assert_household_in_family(data.get("household"), family_id)

    loan_source = data.get("loan_source", LoanSource.INTERNAL)
    lender = data.get("lender")
    if loan_source == LoanSource.INTERNAL:
        if lender is None:
            raise ApplicationError(
                "An internal loan requires a lender who is a family member.", code="lender_required"
            )
        _assert_member_in_family(lender, family_id)
        if lender.id == borrower.id:
            raise ApplicationError(
                "Borrower and lender cannot be the same person.", code="same_party"
            )
    else:
        if not data.get("external_lender_name"):
            raise ApplicationError(
                "An external loan requires an external lender name.",
                code="external_lender_required",
            )
        data["lender"] = None

    interest_amount = calculate_interest(
        interest_type=data.get("interest_type", "none"),
        principal=data["principal_amount"],
        annual_rate=data.get("interest_rate", 0),
        start=data["loan_date"],
        end=data.get("due_date") or data["loan_date"],
    )
    total_amount = data["principal_amount"] + interest_amount

    loan = Loan.objects.create(
        family_id=family_id,
        interest_amount=interest_amount,
        total_amount=total_amount,
        remaining_amount=total_amount,
        status=LoanStatus.ACTIVE,
        created_by=actor,
        updated_by=actor,
        **data,
    )

    ledger_hook.queue_posting(
        family_id=family_id,
        event_type=LedgerPostingEvent.LOAN_CREATED,
        amount=loan.total_amount,
        source_model="Loan",
        source_id=loan.id,
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_CREATED,
        target_model="Loan",
        target_id=loan.id,
        family_id=family_id,
        metadata={"principal": str(loan.principal_amount), "total": str(loan.total_amount)},
    )
    return loan


def update_loan(*, actor, loan: Loan, data: dict) -> Loan:
    for field, value in data.items():
        setattr(loan, field, value)
    loan.updated_by = actor
    loan.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    ledger_hook.queue_posting(
        family_id=loan.family_id,
        event_type=LedgerPostingEvent.LOAN_UPDATED,
        amount=loan.total_amount,
        source_model="Loan",
        source_id=loan.id,
        metadata={"fields": list(data.keys())},
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_UPDATED,
        target_model="Loan",
        target_id=loan.id,
        family_id=loan.family_id,
        metadata={"fields": list(data.keys())},
    )
    return loan


def cancel_loan(*, actor, loan: Loan) -> Loan:
    loan.soft_delete(deleted_by=actor)

    ledger_hook.queue_posting(
        family_id=loan.family_id,
        event_type=LedgerPostingEvent.LOAN_CANCELLED,
        amount=loan.remaining_amount,
        source_model="Loan",
        source_id=loan.id,
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_CANCELLED,
        target_model="Loan",
        target_id=loan.id,
        family_id=loan.family_id,
    )
    return loan


def restore_loan(*, actor, loan: Loan) -> Loan:
    loan.is_deleted = False
    loan.status = LoanStatus.ACTIVE
    loan.deleted_at = None
    loan.deleted_by = None
    loan.updated_by = actor
    loan.save(
        update_fields=[
            "is_deleted",
            "status",
            "deleted_at",
            "deleted_by",
            "updated_by",
            "updated_at",
        ]
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_RESTORED,
        target_model="Loan",
        target_id=loan.id,
        family_id=loan.family_id,
    )
    return loan
