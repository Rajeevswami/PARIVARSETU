"""Reusable field validators shared across serializers."""

import re

from django.core.exceptions import ValidationError

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


def validate_phone_number(value: str) -> None:
    if not PHONE_REGEX.match(value):
        raise ValidationError("Enter a valid phone number in international format.")


def validate_positive_amount(value) -> None:
    if value is None or value <= 0:
        raise ValidationError("Amount must be greater than zero.")


def validate_not_future_date(value) -> None:
    from django.utils import timezone

    if value and value > timezone.now().date():
        raise ValidationError("Date cannot be in the future.")
