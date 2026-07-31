"""Small stateless helpers shared across apps."""

import uuid
from datetime import date


def generate_reference_code(prefix: str) -> str:
    """e.g. generate_reference_code("TXN") -> 'TXN-3F2A9C1B'"""
    return f"{prefix.upper()}-{uuid.uuid4().hex[:8].upper()}"


def current_financial_year() -> str:
    """India's financial year runs Apr–Mar, e.g. '2026-27'."""
    today = date.today()
    start_year = today.year if today.month >= 4 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"
