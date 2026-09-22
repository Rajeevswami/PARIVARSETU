"""Application-layer encryption for secrets stored in the database.

Disk encryption of the Postgres volume is still required. This only protects
JSON blobs such as provider credentials if the database is copied without the key.
"""

import json

from django.conf import settings

PREFIX = "enc:v1:"


def _fernet():
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        return None
    from cryptography.fernet import Fernet

    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_json(value):
    if not isinstance(value, dict) or "_enc" in value or not value:
        return value
    fernet = _fernet()
    if fernet is None:
        return value
    token = fernet.encrypt(json.dumps(value).encode()).decode()
    return {"_enc": f"{PREFIX}{token}"}


def decrypt_json(value):
    if not isinstance(value, dict) or "_enc" not in value:
        return value
    token = value["_enc"]
    if not str(token).startswith(PREFIX):
        return value
    fernet = _fernet()
    if fernet is None:
        return value
    raw = fernet.decrypt(token[len(PREFIX) :].encode())
    return json.loads(raw.decode())
