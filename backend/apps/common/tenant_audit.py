"""Report tenant models that cannot be filtered by family.

A model is scoped when it has a family foreign key, or when a declared parent
path reaches a model that has one. Platform catalogs are not tenant data.
"""

from django.apps import apps

TENANT_APPS = {
    "expenses",
    "loans",
    "borrow_lend",
    "ledger",
    "documents",
    "households",
    "members",
    "notifications",
    "billing",
    "assistant",
}

# Shared product catalog. It is not a family row and must not be queried as one.
PLATFORM_MODELS = {
    "billing.Plan",
}

# Child rows reached only through a parent that carries family_id.
PARENT_PATHS = {
    "expenses.ExpenseParticipant": ("expense",),
    "expenses.ExpenseAttachment": ("expense",),
    "expenses.ExpenseComment": ("expense",),
    "expenses.ExpenseSettlement": ("expense",),
    "ledger.JournalEntry": ("journal",),
    "documents.DocumentVersion": ("document",),
    "notifications.NotificationPreference": ("user",),
}


def _has_family(model) -> bool:
    return any(field.name == "family" for field in model._meta.fields)


def _path_reaches_family(model, path: tuple[str, ...]) -> bool:
    current = model
    for name in path:
        try:
            field = current._meta.get_field(name)
        except Exception:
            return False
        current = getattr(field, "related_model", None)
        if current is None:
            return False
    return _has_family(current)


def models_missing_family_scope() -> list[str]:
    missing = []
    for model in apps.get_models():
        label = model._meta.label
        if model._meta.app_label not in TENANT_APPS or label in PLATFORM_MODELS:
            continue
        if _has_family(model):
            continue
        path = PARENT_PATHS.get(label)
        if path and _path_reaches_family(model, path):
            continue
        missing.append(label)
    return sorted(missing)
