import pytest
from django.core.exceptions import ValidationError

from apps.accounts.validators import PasswordComplexityValidator

validator = PasswordComplexityValidator()


class TestPasswordComplexityValidator:
    def test_accepts_strong_password(self):
        validator.validate("Str0ng!Pass1")  # should not raise

    @pytest.mark.parametrize(
        "password,expected_fragment",
        [
            ("alllowercase1!", "uppercase"),
            ("ALLUPPERCASE1!", "lowercase"),
            ("NoDigitsHere!", "number"),
            ("NoSpecialChar1", "special character"),
        ],
    )
    def test_rejects_password_missing_requirement(self, password, expected_fragment):
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(password)
        assert any(expected_fragment in str(msg) for msg in exc_info.value.messages)

    def test_rejects_password_over_128_chars(self):
        with pytest.raises(ValidationError):
            validator.validate("A1!" + "a" * 130)
