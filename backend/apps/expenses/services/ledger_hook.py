"""
Single write path to LedgerPostingQueue — every expense/settlement event
that must eventually become a journal entry goes through here. This is
the boundary the future Ledger Engine module will consume from; nothing
in this module bypasses it.
"""

from ..models import LedgerPostingQueue


def queue_posting(
    *, expense, event_type: str, amount, metadata: dict | None = None
) -> LedgerPostingQueue:
    return LedgerPostingQueue.objects.create(
        family_id=expense.family_id,
        expense=expense,
        event_type=event_type,
        amount=amount,
        metadata=metadata or {},
    )
