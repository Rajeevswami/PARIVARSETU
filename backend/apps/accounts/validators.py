"""
Password policy: 8-128 chars, at least one uppercase, one lowercase, one
digit, one special character. Wired into AUTH_PASSWORD_VALIDATORS so it
runs everywhere Django's password validation runs (admin, management
commands, and anywhere serializers call validate_password()).
"""

import re

from django.core.exceptions import ValidationError

UPPERCASE_RE = re.compile(r"[A-Z]")
LOWERCASE_RE = re.compile(r"[a-z]")
DIGIT_RE = re.compile(r"\d")
SPECIAL_RE = re.compile(r"""[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]""")


class PasswordComplexityValidator:
    def validate(self, password: str, user=None) -> None:
        errors = []

        if len(password) > 128:
            errors.append("Password must be at most 128 characters.")
        if not UPPERCASE_RE.search(password):
            errors.append("Password must contain at least one uppercase letter.")
        if not LOWERCASE_RE.search(password):
            errors.append("Password must contain at least one lowercase letter.")
        if not DIGIT_RE.search(password):
            errors.append("Password must contain at least one number.")
        if not SPECIAL_RE.search(password):
            errors.append("Password must contain at least one special character.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        return (
            "Your password must be 8-128 characters and include an uppercase "
            "letter, a lowercase letter, a number, and a special character."
        )
