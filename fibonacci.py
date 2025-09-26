def fibonacci_recursive(n):
    """
    Recursive implementation of Fibonacci sequence.
    Returns the nth Fibonacci number.

    Args:
        n (int): Position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_iterative(n):
    """
    Iterative implementation of Fibonacci sequence.
    More efficient than recursive for large n.

    Args:
        n (int): Position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_memoized(n, memo={}):
    """
    Memoized recursive implementation of Fibonacci sequence.
    Combines recursion with caching for better performance.

    Args:
        n (int): Position in the Fibonacci sequence (0-indexed)
        memo (dict): Cache for previously computed values

    Returns:
        int: The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n in memo:
        return memo[n]
    if n <= 1:
        return n

    memo[n] = fibonacci_memoized(n - 1, memo) + fibonacci_memoized(n - 2, memo)
    return memo[n]


def fibonacci_generator(max_n):
    """
    Generator that yields Fibonacci numbers up to the max_n-th number.

    Args:
        max_n (int): Maximum position to generate

    Yields:
        int: Fibonacci numbers in sequence
    """
    a, b = 0, 1
    for i in range(max_n + 1):
        if i == 0:
            yield a
        elif i == 1:
            yield b
        else:
            a, b = b, a + b
            yield b


if __name__ == "__main__":
    # Test the functions
    print("Testing Fibonacci implementations:")
    print()

    # Test with small numbers
    test_values = [0, 1, 2, 3, 4, 5, 10, 15]

    print("Recursive implementation:")
    for n in test_values:
        result = fibonacci_recursive(n)
        print(f"fibonacci_recursive({n}) = {result}")

    print("\nIterative implementation:")
    for n in test_values:
        result = fibonacci_iterative(n)
        print(f"fibonacci_iterative({n}) = {result}")

    print("\nMemoized implementation:")
    for n in test_values:
        result = fibonacci_memoized(n)
        print(f"fibonacci_memoized({n}) = {result}")

    print("\nGenerator implementation (first 10 numbers):")
    fib_gen = fibonacci_generator(9)
    for i, fib_num in enumerate(fib_gen):
        print(f"fibonacci_generator[{i}] = {fib_num}")

    # Performance comparison for larger numbers
    import time

    print("\nPerformance comparison for n=30:")

    # Iterative
    start = time.time()
    result_iter = fibonacci_iterative(30)
    time_iter = time.time() - start
    print(f"Iterative: {result_iter} (Time: {time_iter:.6f}s)")

    # Memoized
    start = time.time()
    result_memo = fibonacci_memoized(30, {})  # Fresh memo
    time_memo = time.time() - start
    print(f"Memoized: {result_memo} (Time: {time_memo:.6f}s)")

    # Note: Recursive would be too slow for n=30, so we skip it
    print("Recursive skipped for n=30 (would be too slow)")
