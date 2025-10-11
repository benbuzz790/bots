def fibonacci(n):
    """
    Calculate the nth Fibonacci number.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    if n <= 1:
        return n

    # Iterative approach for efficiency
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

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    if n <= 1:
        return n

    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_sequence(count):
    """
    Generate a list of the first 'count' Fibonacci numbers.

    Args:
        count (int): Number of Fibonacci numbers to generate

    Returns:
        list: List of Fibonacci numbers
    """
    if count <= 0:
        return []

    sequence = [0]
    if count == 1:
        return sequence

    sequence.append(1)
    for i in range(2, count):
        sequence.append(sequence[i - 1] + sequence[i - 2])

    return sequence


# Example usage
if __name__ == "__main__":
    print("First 10 Fibonacci numbers:")
    print(fibonacci_sequence(10))

    print("\n10th Fibonacci number (iterative):", fibonacci(10))
    print("10th Fibonacci number (recursive):", fibonacci_recursive(10))
