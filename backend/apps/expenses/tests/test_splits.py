"""Pure unit tests for split calculation — no DB needed."""

from decimal import Decimal

import pytest

from apps.common.exceptions import ApplicationError
from apps.expenses.services.splits import (
    calculate_equal_split,
    calculate_fixed_split,
    calculate_percentage_split,
    calculate_shares,
)


class TestEqualSplit:
    def test_splits_evenly_when_divisible(self):
        shares = calculate_equal_split(Decimal("300.00"), ["a", "b", "c"])
        assert shares == {"a": Decimal("100.00"), "b": Decimal("100.00"), "c": Decimal("100.00")}
        assert sum(shares.values()) == Decimal("300.00")

    def test_remainder_goes_to_last_participant(self):
        shares = calculate_equal_split(Decimal("100.00"), ["a", "b", "c"])
        assert sum(shares.values()) == Decimal("100.00")
        assert shares["a"] == Decimal("33.33")
        assert shares["b"] == Decimal("33.33")
        # last participant absorbs the rounding remainder
        assert shares["c"] == Decimal("33.34")

    def test_empty_participant_list_raises(self):
        with pytest.raises(ApplicationError):
            calculate_equal_split(Decimal("100.00"), [])

    def test_single_participant_gets_full_amount(self):
        shares = calculate_equal_split(Decimal("500.00"), ["a"])
        assert shares == {"a": Decimal("500.00")}


class TestPercentageSplit:
    def test_splits_by_percentage(self):
        shares = calculate_percentage_split(Decimal("1000.00"), {"a": 60, "b": 40})
        assert shares["a"] == Decimal("600.00")
        assert shares["b"] == Decimal("400.00")
        assert sum(shares.values()) == Decimal("1000.00")

    def test_percentages_must_sum_to_100(self):
        with pytest.raises(ApplicationError):
            calculate_percentage_split(Decimal("1000.00"), {"a": 60, "b": 30})

    def test_rounding_remainder_absorbed_by_last_participant(self):
        shares = calculate_percentage_split(Decimal("100.00"), {"a": 33.33, "b": 33.33, "c": 33.34})
        assert sum(shares.values()) == Decimal("100.00")

    def test_empty_raises(self):
        with pytest.raises(ApplicationError):
            calculate_percentage_split(Decimal("100.00"), {})


class TestFixedSplit:
    def test_accepts_exact_matching_amounts(self):
        shares = calculate_fixed_split(Decimal("500.00"), {"a": 200, "b": 300})
        assert shares == {"a": Decimal("200.00"), "b": Decimal("300.00")}

    def test_rejects_amounts_that_dont_sum_to_total(self):
        with pytest.raises(ApplicationError):
            calculate_fixed_split(Decimal("500.00"), {"a": 200, "b": 250})

    def test_empty_raises(self):
        with pytest.raises(ApplicationError):
            calculate_fixed_split(Decimal("100.00"), {})


class TestCalculateSharesDispatch:
    def test_equal_dispatch(self):
        shares = calculate_shares(
            split_type="equal", total=Decimal("100.00"), split_data=["a", "b"]
        )
        assert sum(shares.values()) == Decimal("100.00")

    def test_percentage_dispatch(self):
        shares = calculate_shares(
            split_type="percentage", total=Decimal("100.00"), split_data={"a": 100}
        )
        assert shares["a"] == Decimal("100.00")

    def test_fixed_and_custom_behave_identically(self):
        fixed = calculate_shares(split_type="fixed", total=Decimal("100.00"), split_data={"a": 100})
        custom = calculate_shares(
            split_type="custom", total=Decimal("100.00"), split_data={"a": 100}
        )
        assert fixed == custom

    def test_unknown_split_type_raises(self):
        with pytest.raises(ApplicationError):
            calculate_shares(split_type="bogus", total=Decimal("100.00"), split_data={})
