"""Self-service profile operations."""

from apps.audit import services as audit_services


def update_profile(*, user, data: dict, request=None) -> "User":  # noqa: F821
    allowed_fields = {"first_name", "last_name", "gender", "date_of_birth"}
    changed = []

    for field, value in data.items():
        if field in allowed_fields:
            setattr(user, field, value)
            changed.append(field)

    if changed:
        user.save(update_fields=changed + ["updated_at"])
        meta = {"ip_address": None, "user_agent": ""}
        if request is not None:
            meta = {
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
            }
        audit_services.record(
            actor=user,
            action=audit_services.AuditAction.PROFILE_UPDATED,
            metadata={"fields": changed},
            **meta,
        )

    return user


def upload_avatar(*, user, photo_file, request=None) -> "User":  # noqa: F821
    user.profile_photo = photo_file
    user.save(update_fields=["profile_photo", "updated_at"])

    audit_services.record(actor=user, action=audit_services.AuditAction.AVATAR_UPDATED)
    return user
