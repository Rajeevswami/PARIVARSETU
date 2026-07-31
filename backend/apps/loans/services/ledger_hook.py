"""Single write path to this module's LedgerPostingQueue — nothing bypasses it."""

from ..models import LedgerPostingQueue


def queue_posting(
    *,
    family_id,
    event_type: str,
    amount,
    source_model: str,
    source_id,
    metadata: dict | None = None,
) -> LedgerPostingQueue:
    return LedgerPostingQueue.objects.create(
        family_id=family_id,
        event_type=event_type,
        amount=amount,
        source_model=source_model,
        source_id=str(source_id),
        metadata=metadata or {},
    )
