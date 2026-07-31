"""Business logic for ExpenseCategory CRUD."""

from apps.audit import services as audit_services

from ..models import ExpenseCategory


def create_category(*, actor, family_id, data: dict) -> ExpenseCategory:
    category = ExpenseCategory.objects.create(
        family_id=family_id, created_by=actor, updated_by=actor, **data
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_CATEGORY_CREATED,
        target_model="ExpenseCategory",
        target_id=category.id,
        family_id=family_id,
    )
    return category


def update_category(*, actor, category: ExpenseCategory, data: dict) -> ExpenseCategory:
    for field, value in data.items():
        setattr(category, field, value)
    category.updated_by = actor
    category.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_CATEGORY_UPDATED,
        target_model="ExpenseCategory",
        target_id=category.id,
        family_id=category.family_id,
        metadata={"fields": list(data.keys())},
    )
    return category
