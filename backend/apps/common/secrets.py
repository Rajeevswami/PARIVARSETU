"""Secrets come from the environment. Vault is optional and never required to import settings."""

import json
import urllib.request

from django.conf import settings

REQUIRED = ("SECRET_KEY", "FIELD_ENCRYPTION_KEY")


def missing_secret_names() -> list[str]:
    return [name for name in REQUIRED if not getattr(settings, name, "")]


def read_vault(path: str = "familynexus/data/app") -> dict:
    if not settings.VAULT_ADDR or not settings.VAULT_TOKEN:
        return {}
    request = urllib.request.Request(
        f"{settings.VAULT_ADDR.rstrip('/')}/v1/{path}",
        headers={"X-Vault-Token": settings.VAULT_TOKEN},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode())
    return payload.get("data", {}).get("data", {})
