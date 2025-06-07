import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bots.tools.self_tools import _process_string_array, _modify_own_settings
def test_process_string_array():
    """Test the _process_string_array function with handle_errors decorator"""
    print("Testing _process_string_array...")
    # Test valid input
    result = _process_string_array("['hello', 'world', 'test']")
    print(f"Valid input result: {result}")
    assert result == ['hello', 'world', 'test'], f"Expected ['hello', 'world', 'test'], got {result}"
    # Test invalid input (should return error string now instead of raising)
    result = _process_string_array("invalid input")
    print(f"Invalid input result: {result}")
    assert result.startswith("Tool Failed:"), f"Expected error string starting with 'Tool Failed:', got {result}"
    print("✓ _process_string_array tests passed!")
def test_modify_own_settings():
    """Test the _modify_own_settings function with handle_errors decorator"""
    print("Testing _modify_own_settings...")
    # Test with no bot (should return error)
    result = _modify_own_settings(temperature="0.5")
    print(f"No bot result: {result}")
    assert "Error: Could not find calling bot" in result, f"Expected bot error, got {result}"
    # Test with invalid temperature (should return error string instead of raising)
    result = _modify_own_settings(temperature="invalid")
    print(f"Invalid temperature result: {result}")
    assert result.startswith("Tool Failed:"), f"Expected error string starting with 'Tool Failed:', got {result}"
    print("✓ _modify_own_settings tests passed!")
if __name__ == "__main__":
    test_process_string_array()
    test_modify_own_settings()
    print("All tests passed! The handle_errors decorator is working correctly.")
