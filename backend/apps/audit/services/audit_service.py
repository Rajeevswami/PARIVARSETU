"""Single write path for audit events — every module calls this, never the model directly."""

from ..models import AuditAction, AuditLog


def record(
    *,
    actor=None,
    action: str,
    target_model: str = "",
    target_id: str = "",
    family_id=None,
    metadata: dict | None = None,
    ip_address: str | None = None,
    user_agent: str = "",
) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model,
        target_id=str(target_id) if target_id else "",
        family_id=family_id,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent[:255],
    )


__all__ = ["record", "AuditAction"]
