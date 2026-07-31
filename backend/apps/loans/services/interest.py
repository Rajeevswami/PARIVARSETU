"""
Pure interest-calculation logic — no DB access, no side effects. Kept
separate so the math can be unit-tested in isolation.

Rate is always an annual percentage (e.g. 12.00 = 12% per annum).
Duration is derived from (end_date - start_date) in days, converted to
a fraction of a year using a 365-day year.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
DAYS_PER_YEAR = Decimal("365")

COMPOUNDING_PERIODS_PER_YEAR = {
    "monthly": 12,
    "quarterly": 4,
    "annually": 1,
}


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _years_between(start: date, end: date) -> Decimal:
    days = (end - start).days
    if days <= 0:
        return Decimal("0")
    return Decimal(days) / DAYS_PER_YEAR


def calculate_simple_interest(
    principal: Decimal, annual_rate: Decimal, start: date, end: date
) -> Decimal:
    years = _years_between(start, end)
    interest = principal * (annual_rate / Decimal("100")) * years
    return _quantize(interest)


def calculate_compound_interest(
    principal: Decimal,
    annual_rate: Decimal,
    start: date,
    end: date,
    compounding_frequency: str = "annually",
) -> Decimal:
    years = _years_between(start, end)
    n = Decimal(COMPOUNDING_PERIODS_PER_YEAR.get(compounding_frequency, 1))
    if years <= 0 or annual_rate <= 0:
        return Decimal("0.00")

    rate_per_period = (annual_rate / Decimal("100")) / n
    periods = n * years
    # Decimal doesn't support fractional exponents natively; use float for
    # the exponentiation step only, then convert back — fine for currency
    # rounding to 2dp, and avoids pulling in a math dependency for this.
    amount = float(principal) * ((1 + float(rate_per_period)) ** float(periods))
    interest = Decimal(str(amount)) - principal
    return _quantize(interest)


def calculate_interest(
    *,
    interest_type: str,
    principal: Decimal,
    annual_rate: Decimal,
    start: date,
    end: date,
    compounding_frequency: str = "annually",
) -> Decimal:
    if interest_type == "none" or annual_rate <= 0:
        return Decimal("0.00")
    if interest_type == "simple":
        return calculate_simple_interest(principal, annual_rate, start, end)
    if interest_type == "compound":
        return calculate_compound_interest(
            principal, annual_rate, start, end, compounding_frequency
        )
    raise ValueError(f"Unknown interest_type: {interest_type}")
