"""Logical family export for disaster recovery. It does not replace volume snapshots."""

import json
from pathlib import Path

from apps.families.models import Family


def export_family(family: Family, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    payload = {
        "family": {
            "id": str(family.id),
            "family_name": family.family_name,
            "family_code": family.family_code,
            "currency": family.currency,
        },
        "members": list(family.members.filter(is_deleted=False).values("id", "display_name")),
    }
    path = destination / f"{family.family_code}.json"
    path.write_text(json.dumps(payload, default=str), encoding="utf-8")
    return path
