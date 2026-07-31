"""
Business logic for recording loan payments. Splits each payment between
interest and principal (interest-first, standard amortization
convention), updates the loan's running balances, and — unless the loan
has allow_overpayment set — rejects any payment larger than what's
actually owed.
"""

from decimal import Decimal

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import LedgerPostingEvent, Loan, LoanPayment, LoanStatus
from . import ledger_hook


def record_payment(
    *,
    actor,
    loan: Loan,
    amount: Decimal,
    payment_date,
    payment_method: str,
    remarks: str = "",
    attachment=None,
) -> LoanPayment:
    if amount <= 0:
        raise ApplicationError("Payment amount must be greater than zero.", code="invalid_amount")

    if not loan.allow_overpayment and amount > loan.remaining_amount:
        raise ApplicationError(
            f"Payment ({amount}) exceeds the remaining balance ({loan.remaining_amount}). "
            "Enable allow_overpayment on the loan to permit this.",
            code="excess_payment",
        )

    # Interest-first application: any outstanding interest is paid down
    # before principal.
    outstanding_interest = max(loan.interest_amount - _total_interest_paid(loan), Decimal("0"))
    interest_paid = min(amount, outstanding_interest)
    principal_paid = amount - interest_paid

    loan.paid_amount += amount
    loan.remaining_amount = max(loan.total_amount - loan.paid_amount, Decimal("0"))
    if loan.remaining_amount <= 0:
        loan.status = LoanStatus.COMPLETED
    elif loan.status == LoanStatus.ACTIVE:
        loan.status = LoanStatus.RUNNING
    loan.save(update_fields=["paid_amount", "remaining_amount", "status", "updated_at"])

    payment = LoanPayment.objects.create(
        loan=loan,
        payment_date=payment_date,
        amount=amount,
        interest_paid=interest_paid,
        principal_paid=principal_paid,
        remaining_balance=loan.remaining_amount,
        payment_method=payment_method,
        remarks=remarks,
        attachment=attachment,
        created_by=actor,
    )

    ledger_hook.queue_posting(
        family_id=loan.family_id,
        event_type=LedgerPostingEvent.LOAN_PAYMENT_RECORDED,
        amount=amount,
        source_model="LoanPayment",
        source_id=payment.id,
        metadata={"loan_id": str(loan.id)},
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LOAN_PAYMENT_ADDED,
        target_model="LoanPayment",
        target_id=payment.id,
        family_id=loan.family_id,
        metadata={"amount": str(amount)},
    )
    return payment


def _total_interest_paid(loan: Loan) -> Decimal:
    return sum((p.interest_paid for p in loan.payments.all()), Decimal("0"))
