import math
from typing import List, Optional
import math
from typing import List, Optional
import math
from typing import List, Optional
import math
from typing import List, Optional
"""
A sample Python module for demonstrating the python_edit tool.
"""

class Calculator:
    """A simple calculator class with basic operations."""

    def __init__(self, name: str="Basic Calculator"):
        self.name = name
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers with formatted output."""
        a = validate_numeric_input(a)
        b = validate_numeric_input(b)
        result = a + b
        formatted_result = format_number(result)
        self.history.append(f"{format_number(a)} + {format_number(b)} = {formatted_result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        result = math.pow(base, exponent)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result

    def sqrt(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number!")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Return calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()

def main():
    calc = Calculator("Advanced Calculator")
    print(f"Using {calc.name}")
    # Test basic operations
    result1 = calc.add(10, 5)
    result2 = calc.subtract(10, 3)
    result3 = calc.multiply(4, 7)
    result4 = calc.divide(20, 4)
    # Test advanced operations
    result5 = calc.power(2, 3)
    result6 = calc.sqrt(16)
    print(f"Results: {result1}, {result2}, {result3}, {result4}, {result5}, {result6}")
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
    # Test error handling
    try:
        calc.divide(5, 0)
    except ValueError as e:
        print(f"\nError caught: {e}")
    try:
        calc.sqrt(-4)
    except ValueError as e:
        print(f"Error caught: {e}")
    print(f"\nTotal calculations performed: {len(calc.get_history())}")
if __name__ == "__main__":
    main()
"""
A sample Python module for demonstrating the python_edit tool.
"""

class Calculator:
    """A simple calculator class with basic operations."""

    def __init__(self, name: str="Basic Calculator"):
        self.name = name
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers with formatted output."""
        a = validate_numeric_input(a)
        b = validate_numeric_input(b)
        result = a + b
        formatted_result = format_number(result)
        self.history.append(f"{format_number(a)} + {format_number(b)} = {formatted_result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        result = math.pow(base, exponent)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result

    def sqrt(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number!")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Return calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()

def main():
    calc = Calculator("Advanced Calculator")
    print(f"Using {calc.name}")
    # Test basic operations
    result1 = calc.add(10, 5)
    result2 = calc.subtract(10, 3)
    result3 = calc.multiply(4, 7)
    result4 = calc.divide(20, 4)
    # Test advanced operations
    result5 = calc.power(2, 3)
    result6 = calc.sqrt(16)
    print(f"Results: {result1}, {result2}, {result3}, {result4}, {result5}, {result6}")
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
    # Test error handling
    try:
        calc.divide(5, 0)
    except ValueError as e:
        print(f"\nError caught: {e}")
    try:
        calc.sqrt(-4)
    except ValueError as e:
        print(f"Error caught: {e}")
    print(f"\nTotal calculations performed: {len(calc.get_history())}")
if __name__ == "__main__":
    main()
"""
A sample Python module for demonstrating the python_edit tool.
"""

class Calculator:
    """A simple calculator class with basic operations."""

    def __init__(self, name: str="Basic Calculator"):
        self.name = name
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers with formatted output."""
        a = validate_numeric_input(a)
        b = validate_numeric_input(b)
        result = a + b
        formatted_result = format_number(result)
        self.history.append(f"{format_number(a)} + {format_number(b)} = {formatted_result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        result = math.pow(base, exponent)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result

    def sqrt(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number!")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Return calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()

def main():
    calc = Calculator("Advanced Calculator")
    print(f"Using {calc.name}")
    # Test basic operations
    result1 = calc.add(10, 5)
    result2 = calc.subtract(10, 3)
    result3 = calc.multiply(4, 7)
    result4 = calc.divide(20, 4)
    # Test advanced operations
    result5 = calc.power(2, 3)
    result6 = calc.sqrt(16)
    print(f"Results: {result1}, {result2}, {result3}, {result4}, {result5}, {result6}")
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
    # Test error handling
    try:
        calc.divide(5, 0)
    except ValueError as e:
        print(f"\nError caught: {e}")
    try:
        calc.sqrt(-4)
    except ValueError as e:
        print(f"Error caught: {e}")
    print(f"\nTotal calculations performed: {len(calc.get_history())}")
if __name__ == "__main__":
    main()
"""
A sample Python module for demonstrating the python_edit tool.
"""

class Calculator:
    """A simple calculator class with basic operations."""

    def __init__(self, name: str="Basic Calculator"):
        self.name = name
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers with formatted output."""
        a = validate_numeric_input(a)
        b = validate_numeric_input(b)
        result = a + b
        formatted_result = format_number(result)
        self.history.append(f"{format_number(a)} + {format_number(b)} = {formatted_result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        result = math.pow(base, exponent)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result

    def sqrt(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number!")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Return calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()

def main():
    calc = Calculator("Advanced Calculator")
    print(f"Using {calc.name}")
    # Test basic operations
    result1 = calc.add(10, 5)
    result2 = calc.subtract(10, 3)
    result3 = calc.multiply(4, 7)
    result4 = calc.divide(20, 4)
    # Test advanced operations
    result5 = calc.power(2, 3)
    result6 = calc.sqrt(16)
    print(f"Results: {result1}, {result2}, {result3}, {result4}, {result5}, {result6}")
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
    # Test error handling
    try:
        calc.divide(5, 0)
    except ValueError as e:
        print(f"\nError caught: {e}")
    try:
        calc.sqrt(-4)
    except ValueError as e:
        print(f"Error caught: {e}")
    print(f"\nTotal calculations performed: {len(calc.get_history())}")
if __name__ == "__main__":
    main()

def format_number(num: float, precision: int=2) -> str:
    """Format a number to a specified precision."""
    return f"{num:.{precision}f}"

def validate_numeric_input(value) -> float:
    """Validate and convert input to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric input: {value}")