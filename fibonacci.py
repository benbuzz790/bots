def fibonacci(n):
    """
    Calculate the nth Fibonacci number.

    Parameters:
    -----------
    n : int
        The position in the Fibonacci sequence (0-indexed)

    Returns:
    --------
    int
        The nth Fibonacci number

    Examples:
    ---------
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


# Example usage
if __name__ == "__main__":
    print("First 10 Fibonacci numbers:")
    for i in range(10):
        print(f"fibonacci({i}) = {fibonacci(i)}")
