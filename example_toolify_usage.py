"""
Example usage of the @toolify decorator with the bots framework.

This demonstrates how @toolify converts regular functions into
string-in, string-out bot tools with automatic type conversion.
"""

from bots.dev.decorators import toolify


# Basic usage - minimal decoration
@toolify()
def add_numbers(x: int, y: int = 0) -> int:
    """Add two numbers together."""
    return x + y


# Custom description override
@toolify("Calculate the area of a circle given its radius")
def circle_area(radius: float) -> float:
    """Calculate circle area."""
    import math
    return math.pi * radius * radius


# List processing tool
@toolify()
def process_list(items: list, operation: str = "sum") -> float:
    """Process a list of numbers with various operations."""
    if operation == "sum":
        return sum(items)
    elif operation == "average":
        return sum(items) / len(items)
    elif operation == "max":
        return max(items)
    elif operation == "min":
        return min(items)
    else:
        raise ValueError(f"Unknown operation: {operation}")


# Dictionary processing tool
@toolify("Extract and format user information")
def format_user_info(user_data: dict, format_type: str = "simple") -> str:
    """Format user information in different styles."""
    name = user_data.get("name", "Unknown")
    age = user_data.get("age", "Unknown")

    if format_type == "simple":
        return f"{name} ({age})"
    elif format_type == "detailed":
        return f"Name: {name}, Age: {age} years old"
    else:
        return f"User: {name}, {age}"


# Function that returns None (demonstrates automatic message)
@toolify()
def log_message(message: str, level: str = "info") -> None:
    """Log a message at the specified level."""
    print(f"[{level.upper()}] {message}")


# Function without type hints (works with strings)
@toolify("Concatenate strings with a separator")
def join_strings(text1, text2, separator=" "):
    """Join two strings with a separator."""
    return f"{text1}{separator}{text2}"


if __name__ == "__main__":
    print("=== @toolify Decorator Examples ===\n")

    # Test basic math
    print("1. Basic math:")
    result = add_numbers("10", "5")
    print(f"   add_numbers('10', '5') = {result}")
    print()

    # Test with default parameter
    print("2. Default parameter:")
    result = add_numbers("7")
    print(f"   add_numbers('7') = {result}")
    print()

    # Test circle area
    print("3. Circle area:")
    result = circle_area("3.0")
    print(f"   circle_area('3.0') = {result}")
    print()

    # Test list processing
    print("4. List processing:")
    result = process_list("[1, 2, 3, 4, 5]", "average")
    print(f"   process_list('[1, 2, 3, 4, 5]', 'average') = {result}")
    print()

    # Test dictionary processing
    print("5. Dictionary processing:")
    result = format_user_info('{"name": "Alice", "age": 30}', "detailed")
    print(f"   format_user_info(user_dict, 'detailed') = {result}")
    print()

    # Test None return
    print("6. None return:")
    result = log_message("Test message", "debug")
    print(f"   log_message('Test message', 'debug') = {result}")
    print()

    # Test error handling
    print("7. Error handling:")
    result = process_list("[1, 2, 3]", "invalid_operation")
    print(f"   process_list with invalid operation = {result}")
    print()

    # Test function without type hints
    print("8. No type hints:")
    result = join_strings("Hello", "World", " - ")
    print(f"   join_strings('Hello', 'World', ' - ') = {result}")
    print()

    print("All examples completed successfully!")
    print("\nTo use with bots:")
    print("  bot = AnthropicBot()")
    print("  bot.add_tools(add_numbers, circle_area, process_list)")
    print("  response = bot.respond('Calculate the area of a circle with radius 5')")