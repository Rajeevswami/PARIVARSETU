"""Pure helpers for the ParivarSetu → FamilyNexus cutover.

No Django imports, so the shell script and unit tests can use these before
a database or settings module is available.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from config.product import (
    LEGACY_DB_NAME,
    LEGACY_DB_USER,
    LEGACY_PLACEHOLDER_EMAIL_DOMAIN,
    LEGACY_PRODUCT_DOMAIN,
    LEGACY_PRODUCT_NAME,
    PRODUCT_DOMAIN,
    PRODUCT_NAME,
    PRODUCT_SLUG,
)

# Identity keys only. Passwords are never rewritten, even when they equal the
# old role name — renaming the Postgres role keeps the existing password.
_IDENTITY_KEYS = {
    "DB_NAME": (LEGACY_DB_NAME, PRODUCT_SLUG),
    "DB_USER": (LEGACY_DB_USER, PRODUCT_SLUG),
    "POSTGRES_DB": (LEGACY_DB_NAME, PRODUCT_SLUG),
    "POSTGRES_USER": (LEGACY_DB_USER, PRODUCT_SLUG),
}


def rewrite_placeholder_email(email: str, *, new_domain: str) -> str | None:
    """Return the new address, or None when this is not a synthetic placeholder.

    Only ``local@placeholder.parivarsetu.app`` is rewritten. Real mailboxes,
    including any address on the old product domain, are left alone.
    """

    if not email or "@" not in email:
        return None
    local, _, domain = email.rpartition("@")
    if domain.lower() != LEGACY_PLACEHOLDER_EMAIL_DOMAIN or not local or "@" in local:
        return None
    return f"{local}@{new_domain}"


def rewrite_database_url(url: str) -> str:
    """Rename the user and database in a Postgres URL. Leave the password."""

    parts = urlsplit(url)
    if parts.scheme not in {"postgres", "postgresql"} or parts.hostname is None:
        return url
    username = parts.username
    password = parts.password
    database = parts.path.lstrip("/")
    changed = False
    if username == LEGACY_DB_USER:
        username = PRODUCT_SLUG
        changed = True
    if database == LEGACY_DB_NAME:
        database = PRODUCT_SLUG
        changed = True
    if not changed:
        return url

    auth = username or ""
    if password is not None:
        auth = f"{auth}:{password}"
    host = parts.hostname
    if parts.port:
        host = f"{host}:{parts.port}"
    netloc = f"{auth}@{host}" if auth else host
    return urlunsplit((parts.scheme, netloc, f"/{database}", parts.query, parts.fragment))


def rewrite_env_text(text: str) -> tuple[str, list[str]]:
    """Rewrite identity values in a dotenv file. Comments and secrets stay."""

    notes: list[str] = []
    lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            lines.append(line)
            continue
        key, _, raw_value = line.partition("=")
        key = key.strip()
        newline = "\n" if line.endswith("\n") else ""
        value = raw_value[:-1] if newline else raw_value
        if key in _IDENTITY_KEYS:
            old, new = _IDENTITY_KEYS[key]
            unquoted = value.strip().strip("'\"")
            if unquoted == old:
                quote = value.strip()[:1] if value.strip()[:1] in {"'", '"'} else ""
                rewritten = f"{quote}{new}{quote}" if quote else new
                lines.append(f"{key}={rewritten}{newline}")
                notes.append(f"{key}: {old} -> {new}")
                continue
        if key == "DATABASE_URL":
            rewritten = rewrite_database_url(value.strip().strip("'\""))
            if rewritten != value.strip().strip("'\""):
                lines.append(f"{key}={rewritten}{newline}")
                notes.append("DATABASE_URL: renamed user/database, password unchanged")
                continue
        if key == "DEFAULT_FROM_EMAIL":
            rewritten = value.replace(LEGACY_PRODUCT_NAME, PRODUCT_NAME).replace(
                f"@{LEGACY_PRODUCT_DOMAIN}", f"@{PRODUCT_DOMAIN}"
            )
            if rewritten != value:
                lines.append(f"{key}={rewritten}{newline}")
                notes.append("DEFAULT_FROM_EMAIL: product name and domain updated")
                continue
        lines.append(line)
    trailing_newline = text.endswith("\n") or text == ""
    rewritten_text = "".join(lines)
    if trailing_newline and rewritten_text and not rewritten_text.endswith("\n"):
        rewritten_text += "\n"
    return rewritten_text, notes


def rewrite_env_file(path: Path, *, dry_run: bool = False) -> list[str]:
    original = path.read_text()
    rewritten, notes = rewrite_env_text(original)
    if notes and not dry_run:
        path.write_text(rewritten)
    return notes
