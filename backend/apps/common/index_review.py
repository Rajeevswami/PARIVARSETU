"""Family-scoped queries should have an index that starts with family."""

from django.apps import apps


def family_indexes_missing() -> list[str]:
    missing = []
    for model in apps.get_models():
        if not any(field.name == "family" for field in model._meta.fields):
            continue
        indexed = False
        for index in model._meta.indexes:
            if index.fields and index.fields[0].lstrip("-") == "family":
                indexed = True
        if any(field.name == "family" and field.db_index for field in model._meta.fields):
            indexed = True
        if not indexed:
            missing.append(model._meta.label)
    return sorted(missing)
