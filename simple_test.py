import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bots.tools.self_tools import _process_string_array
def test_decorator():
    print("Testing handle_errors decorator...")
    # Test valid input
    result = _process_string_array("['hello', 'world']")
    print(f"Valid: {result}")
    # Test invalid input - should return error string instead of raising
    result = _process_string_array("invalid")
    print(f"Invalid: {result}")
    if result.startswith("Tool Failed:"):
        print("✓ Decorator working correctly!")
    else:
        print("✗ Decorator not working as expected")
if __name__ == "__main__":
    test_decorator()
