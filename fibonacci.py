def fibonacci_recursive(n):
    """
    Calculate the nth Fibonacci number using recursion.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number

    Note: This is inefficient for large n due to repeated calculations.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_iterative(n):
    """
    Calculate the nth Fibonacci number using iteration.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)

    Returns:
        int: The nth Fibonacci number

    Note: This is efficient with O(n) time complexity and O(1) space complexity.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = (0, 1)
    for _ in range(2, n + 1):
        a, b = (b, a + b)
    return b

def fibonacci_memoized(n, memo=None):
    """
    Calculate the nth Fibonacci number using memoization.

    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)
        memo (dict): Dictionary to store previously calculated values

    Returns:
        int: The nth Fibonacci number

    Note: This combines the elegance of recursion with efficiency.
    """
    if memo is None:
        memo = {}
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fibonacci_memoized(n - 1, memo) + fibonacci_memoized(n - 2, memo)
    return memo[n]

def fibonacci_sequence(count):
    """
    Generate a sequence of Fibonacci numbers.

    Args:
        count (int): Number of Fibonacci numbers to generate

    Returns:
        list: List of the first 'count' Fibonacci numbers
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    if count == 0:
        return []
    if count == 1:
        return [0]
    sequence = [0, 1]
    for i in range(2, count):
        sequence.append(sequence[i - 1] + sequence[i - 2])
    return sequence

def fibonacci_generator(count=None):
    """
    Generator function for Fibonacci numbers.

    Args:
        count (int, optional): Maximum number of Fibonacci numbers to generate.
                              If None, generates indefinitely.

    Yields:
        int: Next Fibonacci number in the sequence
    """
    a, b = (0, 1)
    generated = 0
    while count is None or generated < count:
        yield a
        a, b = (b, a + b)
        generated += 1
# Example usage and testing
if __name__ == "__main__":
    # Test the functions
    print("Testing Fibonacci functions:")
    print()
    # Test individual functions
    n = 10
    print(f"fibonacci_recursive({n}) = {fibonacci_recursive(n)}")
    print(f"fibonacci_iterative({n}) = {fibonacci_iterative(n)}")
    print(f"fibonacci_memoized({n}) = {fibonacci_memoized(n)}")
    print()
    # Test sequence generation
    print(f"First 15 Fibonacci numbers: {fibonacci_sequence(15)}")
    print()
    # Test generator
    print("Using generator for first 10 numbers:")
    fib_gen = fibonacci_generator(10)
    for i, fib_num in enumerate(fib_gen):
        print(f"F({i}) = {fib_num}")
    print()
    # Performance comparison for larger numbers
    import time
    n = 35
    print(f"Performance comparison for n={n}:")
    # Iterative (fastest)
    start = time.time()
    result_iter = fibonacci_iterative(n)
    time_iter = time.time() - start
    print(f"Iterative: {result_iter} (Time: {time_iter:.6f}s)")
    # Memoized (fast)
    start = time.time()
    result_memo = fibonacci_memoized(n)
    time_memo = time.time() - start
    print(f"Memoized: {result_memo} (Time: {time_memo:.6f}s)")
    # Note: Recursive would be very slow for n=35, so we'll test with smaller n
    n_small = 20
    start = time.time()
    result_rec = fibonacci_recursive(n_small)
    time_rec = time.time() - start
    print(f"Recursive (n={n_small}): {result_rec} (Time: {time_rec:.6f}s)")