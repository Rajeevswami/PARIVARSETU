"""Export and deletion stay in services. Views only authenticate and return the envelope."""

from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..content import PRIVACY, PRIVACY_VERSION, TERMS, TERMS_VERSION
from ..models import CookieConsent, DataExportRequest, DeletionRequest, LegalAcceptance

DOCUMENTS = {
    "terms": {"version": TERMS_VERSION, "body": TERMS},
    "privacy": {"version": PRIVACY_VERSION, "body": PRIVACY},
}


def documents() -> dict:
    return DOCUMENTS


def record_consent(
    *, user, anonymous_id: str = "", analytics: bool, marketing: bool
) -> CookieConsent:
    consent = CookieConsent.objects.create(
        user=user,
        anonymous_id=anonymous_id,
        analytics=analytics,
        marketing=marketing,
        policy_version=PRIVACY_VERSION,
    )
    if user is not None:
        audit_services.record(
            actor=user,
            action="consent_recorded",
            target_model="CookieConsent",
            target_id=consent.id,
            family_id=getattr(user, "family_id", None),
            metadata={"analytics": analytics, "marketing": marketing},
        )
    return consent


def accept(*, user, document: str) -> LegalAcceptance:
    spec = DOCUMENTS.get(document)
    if spec is None:
        raise ApplicationError("Unknown legal document.", code="unknown_document")
    acceptance, _created = LegalAcceptance.objects.get_or_create(
        user=user, document=document, version=spec["version"]
    )
    return acceptance


def export_user(user) -> dict:
    from apps.expenses.models import Expense
    from apps.notifications.models import Notification

    expenses = []
    if user.family_id:
        expenses = list(
            Expense.objects.filter(
                family_id=user.family_id, created_by=user, is_deleted=False
            ).values("id", "title", "amount", "expense_date", "status")[:500]
        )
    payload = {
        "exported_at": timezone.now().isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
        },
        "expenses_created": expenses,
        "notifications": list(
            Notification.objects.filter(recipient=user).values("title", "message", "created_at")[
                :200
            ]
        ),
    }
    request = DataExportRequest.objects.create(user=user, payload=payload)
    audit_services.record(
        actor=user,
        action="data_export_requested",
        target_model="DataExportRequest",
        target_id=request.id,
        family_id=user.family_id,
    )
    return payload


def delete_account(*, user, reason: str = "") -> None:
    if user.is_staff:
        raise ApplicationError(
            "Staff accounts cannot be self-deleted here.", code="staff_account", status_code=403
        )
    user.email = f"deleted-{user.id.hex[:12]}@placeholder.familynexus.app"
    user.first_name = "Deleted"
    user.last_name = ""
    user.mobile = None
    user.is_active = False
    user.soft_delete(deleted_by=user)
    user.save(update_fields=["email", "first_name", "last_name", "mobile"])
    request = DeletionRequest.objects.create(user=user, reason=reason)
    audit_services.record(
        actor=user,
        action="data_deletion_requested",
        target_model="DeletionRequest",
        target_id=request.id,
        family_id=user.family_id,
    )
