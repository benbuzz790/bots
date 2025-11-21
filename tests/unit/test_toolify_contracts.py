"""Tests for toolify decorator with contract support."""

from bots.dev.decorators import toolify

# Skip the input_with_esc fixture for these unit tests
pytestmark = []


def test_toolify_without_contracts():
    """Test that toolify works without any contracts (backward compatibility)."""

    @toolify()
    def simple_function(x: int, y: int) -> int:
        return x + y

    result = simple_function("5", "3")
    assert result == "8"


def test_toolify_with_precondition_pass():
    """Test that tool executes when precondition passes."""

    def check_positive(x: int, y: int) -> tuple[bool, str]:
        if x > 0 and y > 0:
            return True, ""
        return False, "Both numbers must be positive"

    @toolify(preconditions=[check_positive])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    result = add_numbers("5", "3")
    assert result == "8"


def test_toolify_with_precondition_fail():
    """Test that tool returns error when precondition fails."""

    def check_positive(x: int, y: int) -> tuple[bool, str]:
        if x > 0 and y > 0:
            return True, ""
        return False, "Both numbers must be positive"

    @toolify(preconditions=[check_positive])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    result = add_numbers("-5", "3")
    assert "Contract validation failed" in result
    assert "Both numbers must be positive" in result


def test_toolify_with_postcondition_pass():
    """Test that tool executes when postcondition passes."""

    def result_not_zero(x: int, y: int) -> tuple[bool, str]:
        if x + y != 0:
            return True, ""
        return False, "Result would be zero"

    @toolify(postconditions=[result_not_zero])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    result = add_numbers("5", "3")
    assert result == "8"


def test_toolify_with_postcondition_fail():
    """Test that tool returns error when postcondition fails."""

    def result_not_zero(x: int, y: int) -> tuple[bool, str]:
        if x + y != 0:
            return True, ""
        return False, "Result would be zero"

    @toolify(postconditions=[result_not_zero])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    result = add_numbers("5", "-5")
    assert "Contract validation failed" in result
    assert "Result would be zero" in result


def test_toolify_with_multiple_contracts():
    """Test that multiple contracts are all checked."""

    def check_positive(x: int, y: int) -> tuple[bool, str]:
        if x > 0 and y > 0:
            return True, ""
        return False, "Both numbers must be positive"

    def check_not_too_large(x: int, y: int) -> tuple[bool, str]:
        if x < 100 and y < 100:
            return True, ""
        return False, "Numbers must be less than 100"

    @toolify(preconditions=[check_positive, check_not_too_large])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    # Should pass both
    result = add_numbers("5", "3")
    assert result == "8"

    # Should fail first check
    result = add_numbers("-5", "3")
    assert "Both numbers must be positive" in result

    # Should fail second check
    result = add_numbers("150", "3")
    assert "Numbers must be less than 100" in result


def test_toolify_with_exception_in_contract():
    """Test that exceptions in contracts are handled gracefully."""

    def buggy_contract(x: int, y: int) -> tuple[bool, str]:
        raise ValueError("Contract implementation error")

    @toolify(preconditions=[buggy_contract])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    result = add_numbers("5", "3")
    assert "Tool Failed" in result
    assert "Contract implementation error" in result


def test_toolify_with_both_pre_and_post():
    """Test that both preconditions and postconditions work together."""

    def check_positive(x: int, y: int) -> tuple[bool, str]:
        if x > 0 and y > 0:
            return True, ""
        return False, "Inputs must be positive"

    def result_less_than_20(x: int, y: int) -> tuple[bool, str]:
        if x + y < 20:
            return True, ""
        return False, "Result would exceed 20"

    @toolify(preconditions=[check_positive], postconditions=[result_less_than_20])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    # Should pass both
    result = add_numbers("5", "3")
    assert result == "8"

    # Should fail precondition
    result = add_numbers("-5", "3")
    assert "Inputs must be positive" in result

    # Should fail postcondition
    result = add_numbers("15", "10")
    assert "Result would exceed 20" in result


def test_toolify_with_description_and_contracts():
    """Test that description parameter works with contracts."""

    def check_positive(x: int, y: int) -> tuple[bool, str]:
        if x > 0 and y > 0:
            return True, ""
        return False, "Both numbers must be positive"

    @toolify(description="Add two positive numbers", preconditions=[check_positive])
    def add_numbers(x: int, y: int) -> int:
        return x + y

    assert add_numbers.__doc__ == "Add two positive numbers"
    result = add_numbers("5", "3")
    assert result == "8"
