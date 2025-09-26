def fibonacci_recursive(n):
    """
    Recursive implementation of Fibonacci sequence.
    Returns the nth Fibonacci number.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_iterative(n):
    """
    Iterative implementation of Fibonacci sequence.
    More efficient than recursive for larger values.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_generator(limit):
    """
    Generator that yields Fibonacci numbers up to the limit.
    """
    a, b = 0, 1
    while a <= limit:
        yield a
        a, b = b, a + b


def fibonacci_sequence(n):
    """
    Returns a list of the first n Fibonacci numbers.
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence


# Example usage and testing
if __name__ == "__main__":
    print("Fibonacci Functions Demo")
    print("=" * 30)

    # Test with n = 10
    n = 10
    print(f"\nFibonacci number at position {n}:")
    print(f"Recursive: {fibonacci_recursive(n)}")
    print(f"Iterative: {fibonacci_iterative(n)}")

    # Show first 10 Fibonacci numbers
    print(f"\nFirst {n} Fibonacci numbers:")
    print(fibonacci_sequence(n))

    # Generator example - numbers up to 100
    print("\nFibonacci numbers up to 100:")
    fib_gen = list(fibonacci_generator(100))
    print(fib_gen)

    # Performance comparison for larger numbers
    import time

    n_large = 30
    print(f"\nPerformance comparison for n={n_large}:")

    start = time.time()
    result_iter = fibonacci_iterative(n_large)
    time_iter = time.time() - start

    start = time.time()
    result_rec = fibonacci_recursive(n_large)
    time_rec = time.time() - start

    print(f"Iterative: {result_iter} (Time: {time_iter:.6f}s)")
    print(f"Recursive: {result_rec} (Time: {time_rec:.6f}s)")
