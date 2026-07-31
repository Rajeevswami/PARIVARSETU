"""Pure unit tests for interest calculation — no DB needed."""

from datetime import date
from decimal import Decimal

from apps.loans.services.interest import (
    calculate_compound_interest,
    calculate_interest,
    calculate_simple_interest,
)


class TestSimpleInterest:
    def test_one_year_at_12_percent(self):
        interest = calculate_simple_interest(
            Decimal("10000"), Decimal("12"), date(2025, 1, 1), date(2026, 1, 1)
        )
        assert interest == Decimal("1200.00")

    def test_half_year_at_12_percent(self):
        interest = calculate_simple_interest(
            Decimal("10000"), Decimal("12"), date(2025, 1, 1), date(2025, 7, 2)
        )
        # ~182 days / 365 * 12% * 10000
        assert Decimal("590") < interest < Decimal("600")

    def test_zero_rate_gives_zero_interest(self):
        interest = calculate_simple_interest(
            Decimal("10000"), Decimal("0"), date(2025, 1, 1), date(2026, 1, 1)
        )
        assert interest == Decimal("0.00")

    def test_same_start_and_end_date_gives_zero_interest(self):
        interest = calculate_simple_interest(
            Decimal("10000"), Decimal("12"), date(2025, 1, 1), date(2025, 1, 1)
        )
        assert interest == Decimal("0.00")


class TestCompoundInterest:
    def test_compound_exceeds_simple_over_multiple_years(self):
        simple = calculate_simple_interest(
            Decimal("10000"), Decimal("10"), date(2020, 1, 1), date(2025, 1, 1)
        )
        compound = calculate_compound_interest(
            Decimal("10000"), Decimal("10"), date(2020, 1, 1), date(2025, 1, 1), "annually"
        )
        assert compound > simple

    def test_monthly_compounding_exceeds_annual_compounding(self):
        annual = calculate_compound_interest(
            Decimal("10000"), Decimal("12"), date(2025, 1, 1), date(2026, 1, 1), "annually"
        )
        monthly = calculate_compound_interest(
            Decimal("10000"), Decimal("12"), date(2025, 1, 1), date(2026, 1, 1), "monthly"
        )
        assert monthly > annual

    def test_zero_rate_gives_zero_interest(self):
        interest = calculate_compound_interest(
            Decimal("10000"), Decimal("0"), date(2025, 1, 1), date(2026, 1, 1)
        )
        assert interest == Decimal("0.00")


class TestCalculateInterestDispatch:
    def test_none_type_gives_zero_regardless_of_rate(self):
        interest = calculate_interest(
            interest_type="none",
            principal=Decimal("10000"),
            annual_rate=Decimal("50"),
            start=date(2025, 1, 1),
            end=date(2026, 1, 1),
        )
        assert interest == Decimal("0.00")

    def test_simple_dispatch(self):
        interest = calculate_interest(
            interest_type="simple",
            principal=Decimal("10000"),
            annual_rate=Decimal("12"),
            start=date(2025, 1, 1),
            end=date(2026, 1, 1),
        )
        assert interest == Decimal("1200.00")

    def test_compound_dispatch(self):
        interest = calculate_interest(
            interest_type="compound",
            principal=Decimal("10000"),
            annual_rate=Decimal("12"),
            start=date(2025, 1, 1),
            end=date(2026, 1, 1),
            compounding_frequency="monthly",
        )
        assert interest > Decimal("1200.00")

    def test_unknown_type_raises(self):
        import pytest

        with pytest.raises(ValueError):
            calculate_interest(
                interest_type="bogus",
                principal=Decimal("10000"),
                annual_rate=Decimal("12"),
                start=date(2025, 1, 1),
                end=date(2026, 1, 1),
            )
