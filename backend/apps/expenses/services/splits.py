"""
Pure split-calculation logic — no DB access, no side effects. Kept
separate so split math can be unit-tested without spinning up the DB.

All four split types funnel through here:
- EQUAL: amount divided evenly; any leftover paisa from rounding goes to
  the last participant so shares always sum exactly to the total.
- PERCENTAGE: each member's share = amount * pct/100, rounded to 2dp;
  same last-participant remainder correction.
- FIXED / CUSTOM: caller supplies exact amounts directly; both behave
  identically here (CUSTOM is a distinct spec'd split type but has no
  different math from FIXED — the difference is purely how the frontend
  presents the entry form).
"""

from decimal import ROUND_HALF_UP, Decimal

from apps.common.exceptions import ApplicationError

TWO_PLACES = Decimal("0.01")


class SplitType:
    EQUAL = "equal"
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    CUSTOM = "custom"

    ALL = (EQUAL, PERCENTAGE, FIXED, CUSTOM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_equal_split(total: Decimal, member_ids: list) -> dict:
    if not member_ids:
        raise ApplicationError("At least one participant is required.", code="no_participants")

    count = len(member_ids)
    base_share = _quantize(total / count)
    shares = {member_id: base_share for member_id in member_ids}

    # Correct rounding drift on the last participant so shares sum exactly.
    remainder = total - (base_share * count)
    if remainder != 0:
        last_id = member_ids[-1]
        shares[last_id] = _quantize(shares[last_id] + remainder)

    return shares


def calculate_percentage_split(total: Decimal, member_percentages: dict) -> dict:
    if not member_percentages:
        raise ApplicationError("At least one participant is required.", code="no_participants")

    pct_sum = sum(Decimal(str(p)) for p in member_percentages.values())
    if abs(pct_sum - Decimal("100")) > Decimal("0.01"):
        raise ApplicationError(
            f"Percentages must sum to 100 (got {pct_sum}).", code="invalid_percentage_split"
        )

    shares = {}
    running_total = Decimal("0")
    member_ids = list(member_percentages.keys())
    for member_id in member_ids[:-1]:
        share = _quantize(total * Decimal(str(member_percentages[member_id])) / Decimal("100"))
        shares[member_id] = share
        running_total += share

    # Last participant absorbs the rounding remainder.
    shares[member_ids[-1]] = _quantize(total - running_total)
    return shares


def calculate_fixed_split(total: Decimal, member_amounts: dict) -> dict:
    if not member_amounts:
        raise ApplicationError("At least one participant is required.", code="no_participants")

    shares = {
        member_id: _quantize(Decimal(str(amount))) for member_id, amount in member_amounts.items()
    }
    shares_sum = sum(shares.values())

    if shares_sum != _quantize(total):
        raise ApplicationError(
            f"Participant shares ({shares_sum}) must sum to the expense amount ({total}).",
            code="invalid_fixed_split",
        )
    return shares


def calculate_shares(*, split_type: str, total: Decimal, split_data) -> dict:
    """
    Dispatches to the right calculator.
    - EQUAL: split_data is a list of member_ids
    - PERCENTAGE: split_data is {member_id: percentage}
    - FIXED / CUSTOM: split_data is {member_id: amount}
    Returns {member_id: Decimal(share_amount)}.
    """
    if split_type == SplitType.EQUAL:
        return calculate_equal_split(total, split_data)
    if split_type == SplitType.PERCENTAGE:
        return calculate_percentage_split(total, split_data)
    if split_type in (SplitType.FIXED, SplitType.CUSTOM):
        return calculate_fixed_split(total, split_data)
    raise ApplicationError(f"Unknown split type: {split_type}", code="invalid_split_type")
