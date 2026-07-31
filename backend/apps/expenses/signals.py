"""
Seeds each new Family with a default set of expense categories
("EXPENSE TYPES" in the spec: Personal, Household, Medical, ...).

Lives entirely in apps.expenses, watching apps.families.Family via a
signal — this is the only way this module touches Family creation
without editing a single line of the (already complete) families app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.families.models import Family

from .models import ExpenseCategory

DEFAULT_CATEGORIES = [
    ("Personal", "#0ea5e9"),
    ("Household", "#22c55e"),
    ("Entire Family", "#a855f7"),
    ("Medical", "#ef4444"),
    ("Education", "#f59e0b"),
    ("Travel", "#06b6d4"),
    ("Utilities", "#84cc16"),
    ("Food", "#f97316"),
    ("Shopping", "#ec4899"),
    ("Maintenance", "#64748b"),
    ("Festival", "#eab308"),
    ("Other", "#6b7280"),
]


@receiver(post_save, sender=Family)
def seed_default_expense_categories(sender, instance: Family, created: bool, **kwargs):
    if not created:
        return
    ExpenseCategory.objects.bulk_create(
        [
            ExpenseCategory(family=instance, name=name, color=color, sort_order=i)
            for i, (name, color) in enumerate(DEFAULT_CATEGORIES)
        ]
    )
