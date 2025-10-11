def fibonacci(n):
    """
    Calculate the nth Fibonacci number.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(10)
        55
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


def fibonacci_recursive(n):
    """
    Calculate the nth Fibonacci number using recursion.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number

    Note: This is less efficient than the iterative version for large n.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    elif n <= 1:
        return n
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_sequence(count):
    """
    Generate a list of the first 'count' Fibonacci numbers.

    Args:
        count (int): Number of Fibonacci numbers to generate

    Returns:
        list: List of Fibonacci numbers

    Example:
        >>> fibonacci_sequence(10)
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    """
    if count <= 0:
        return []
    elif count == 1:
        return [0]

    sequence = [0, 1]
    for i in range(2, count):
        sequence.append(sequence[i - 1] + sequence[i - 2])

    return sequence


if __name__ == "__main__":
    # Test the functions
    print("First 15 Fibonacci numbers:")
    print(fibonacci_sequence(15))

    print("\nIndividual Fibonacci numbers:")
    for i in range(10):
        print(f"fibonacci({i}) = {fibonacci(i)}")
