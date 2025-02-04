from typing import Union, Optional
from math import sqrt


def hello_world(name: Optional[str] = "World") -> None:
    """Greet someone by name.

    Args:
        name: Name of person to greet, defaults to "World"
    """
    print(f'Hello {name}!')


def add_numbers(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
    """Add two numbers and return their sum.

    Args:
        x: First number
        y: Second number
    Returns:
        The sum of x and y
    """
    return x + y


class Calculator:
    """A simple calculator class that maintains a running value."""

    def __init__(self, initial_value: Union[int, float] = 0):
        """Initialize calculator with a starting value."""
        self.value = initial_value

    def add(self, x: Union[int, float]) -> float:
        """Add a number to current value."""
        self.value += x
        return self.value

    def subtract(self, x: Union[int, float]) -> float:
        """Subtract a number from current value."""
        self.value -= x
        return self.value
