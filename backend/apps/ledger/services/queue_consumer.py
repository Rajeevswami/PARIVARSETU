"""
Consumes apps.expenses.LedgerPostingQueue and apps.loans.LedgerPostingQueue
— the actual integration point that makes "every financial operation
passes through the Ledger" real. Zero changes to the expenses/loans
modules: they already write to their own queues (built for exactly
this in Modules 5/6); this module reads them.

Idempotent: only ever processes rows with status="pending" and flips
them to "posted" (or "failed" with the error recorded) as it goes, so
re-running this is always safe.
"""

import logging

from django.db import transaction

from ..models import LedgerAccount, TransactionType
from . import journal_service, posting_rules, posting_service

logger = logging.getLogger("apps.errors")


def _account_id_map(family_id) -> dict:
    return dict(LedgerAccount.objects.filter(family_id=family_id).values_list("account_code", "id"))


def _lines_with_account_ids(lines: list[dict], account_map: dict) -> list[dict]:
    resolved = []
    for line in lines:
        account_id = account_map.get(line["account_code"])
        if account_id is None:
            raise ValueError(f"No ledger account with code {line['account_code']} for this family.")
        resolved.append(
            {
                "ledger_account": account_id,
                "entry_type": line["entry_type"],
                "amount": line["amount"],
                "description": line["description"],
            }
        )
    return resolved


def _post(
    *, family_id, transaction_type, journal_date, lines, reference_type, reference_id, description
):
    account_map = _account_id_map(family_id)
    resolved_lines = _lines_with_account_ids(lines, account_map)
    journal = journal_service.create_journal(
        family_id=family_id,
        transaction_type=transaction_type,
        journal_date=journal_date,
        lines=resolved_lines,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )
    posting_service.post_journal(actor=None, journal=journal)
    return journal


@transaction.atomic
def _process_expense_queue_item(item) -> bool:
    from apps.expenses.models import LedgerPostingEvent as ExpenseEvent

    expense = item.expense
    if item.event_type == ExpenseEvent.EXPENSE_CREATED:
        lines = posting_rules.expense_created_lines(
            amount=item.amount, payment_method=expense.payment_method, title=expense.title
        )
    elif item.event_type == ExpenseEvent.EXPENSE_CANCELLED:
        lines = posting_rules.expense_cancelled_lines(
            amount=item.amount, payment_method=expense.payment_method, title=expense.title
        )
    elif item.event_type == ExpenseEvent.SETTLEMENT_RECORDED:
        lines = posting_rules.expense_settlement_lines(amount=item.amount)
    else:
        # EXPENSE_UPDATED and anything else with no distinct balance impact —
        # acknowledged, no journal needed.
        return True

    _post(
        family_id=item.family_id,
        transaction_type=(
            TransactionType.EXPENSE_SETTLEMENT
            if item.event_type == ExpenseEvent.SETTLEMENT_RECORDED
            else TransactionType.EXPENSE
        ),
        journal_date=expense.expense_date,
        lines=lines,
        reference_type="Expense",
        reference_id=str(expense.id),
        description=f"{item.event_type} — {expense.title}",
    )
    return True


@transaction.atomic
def _process_loan_queue_item(item) -> bool:
    from apps.loans.models import LedgerPostingEvent as LoanEvent

    if item.event_type == LoanEvent.LOAN_CREATED:
        loan = _loan_from_source(item)
        lines = posting_rules.loan_created_lines(amount=item.amount, title=loan.title)
        journal_date = loan.loan_date
    elif item.event_type == LoanEvent.LOAN_CANCELLED:
        loan = _loan_from_source(item)
        lines = posting_rules.loan_cancelled_lines(amount=item.amount, title=loan.title)
        journal_date = loan.loan_date
    elif item.event_type == LoanEvent.LOAN_PAYMENT_RECORDED:
        from apps.loans.models import LoanPayment

        payment = LoanPayment.objects.get(id=item.source_id)
        lines = posting_rules.loan_payment_lines(
            principal_paid=payment.principal_paid,
            interest_paid=payment.interest_paid,
            payment_method=payment.payment_method,
        )
        journal_date = payment.payment_date
    elif item.event_type == LoanEvent.BORROW_ENTRY:
        lines = posting_rules.borrow_entry_lines(amount=item.amount)
        journal_date = _borrow_lend_date(item)
    elif item.event_type == LoanEvent.LEND_ENTRY:
        lines = posting_rules.lend_entry_lines(amount=item.amount)
        journal_date = _borrow_lend_date(item)
    elif item.event_type == LoanEvent.SETTLEMENT_RECORDED:
        reference_type = item.metadata.get("reference_type")
        lines = (
            posting_rules.borrow_settlement_lines(amount=item.amount)
            if reference_type == "borrow"
            else posting_rules.lend_settlement_lines(amount=item.amount)
        )
        journal_date = _settlement_date(item)
    else:
        return True

    if not lines:
        return True

    _post(
        family_id=item.family_id,
        transaction_type=_loan_event_to_transaction_type(item.event_type),
        journal_date=journal_date,
        lines=lines,
        reference_type=item.source_model,
        reference_id=item.source_id,
        description=f"{item.event_type} — {item.source_model} {item.source_id}",
    )
    return True


def _loan_event_to_transaction_type(event_type: str) -> str:
    from apps.loans.models import LedgerPostingEvent as LoanEvent

    return {
        LoanEvent.LOAN_CREATED: TransactionType.LOAN_CREATION,
        LoanEvent.LOAN_CANCELLED: TransactionType.LOAN_CREATION,
        LoanEvent.LOAN_PAYMENT_RECORDED: TransactionType.LOAN_PAYMENT,
        LoanEvent.BORROW_ENTRY: TransactionType.BORROW,
        LoanEvent.LEND_ENTRY: TransactionType.LEND,
        LoanEvent.SETTLEMENT_RECORDED: TransactionType.ADJUSTMENT,
    }.get(event_type, TransactionType.ADJUSTMENT)


def _loan_from_source(item):
    from apps.loans.models import Loan

    return Loan.objects.get(id=item.source_id)


def _borrow_lend_date(item):
    from apps.borrow_lend.models import BorrowTransaction, LendTransaction

    if item.source_model == "BorrowTransaction":
        return BorrowTransaction.objects.get(id=item.source_id).date
    return LendTransaction.objects.get(id=item.source_id).date


def _settlement_date(item):
    from apps.borrow_lend.models import Settlement

    return Settlement.objects.get(id=item.source_id).settlement_date


def process_pending_postings() -> dict:
    """Entry point — run this (via Celery task or management command) to drain both queues."""
    from apps.expenses.models import LedgerPostingQueue as ExpenseQueue
    from apps.expenses.models import LedgerPostingStatus as ExpenseStatus
    from apps.loans.models import LedgerPostingQueue as LoanQueue
    from apps.loans.models import LedgerPostingStatus as LoanStatus

    processed = 0
    failed = 0

    for item in ExpenseQueue.objects.filter(status=ExpenseStatus.PENDING).select_related("expense"):
        try:
            _process_expense_queue_item(item)
            item.status = ExpenseStatus.POSTED
            item.save(update_fields=["status"])
            processed += 1
        except Exception:
            logger.exception("Failed to process expense ledger queue item %s", item.id)
            failed += 1

    for item in LoanQueue.objects.filter(status=LoanStatus.PENDING):
        try:
            _process_loan_queue_item(item)
            item.status = LoanStatus.POSTED
            item.save(update_fields=["status"])
            processed += 1
        except Exception:
            logger.exception("Failed to process loan ledger queue item %s", item.id)
            failed += 1

    return {"processed": processed, "failed": failed}
