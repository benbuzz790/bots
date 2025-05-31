import random
import time
from typing import List, Callable

def bubble_sort(arr: List[int]) -> List[int]:
    """
    Bubble Sort - O(n²) time complexity, O(1) space complexity

    Repeatedly steps through the list, compares adjacent elements and swaps them
    if they are in the wrong order.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    arr = arr.copy()  # Don't modify original
    n = len(arr)
    for i in range(n):
        # Flag to optimize - if no swaps occur, array is sorted
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = (arr[j + 1], arr[j])
                swapped = True
        if not swapped:
            break
    return arr

def selection_sort(arr: List[int]) -> List[int]:
    """
    Selection Sort - O(n²) time complexity, O(1) space complexity

    Finds the minimum element and places it at the beginning, then repeats
    for the remaining unsorted portion.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = (arr[min_idx], arr[i])
    return arr

def insertion_sort(arr: List[int]) -> List[int]:
    """
    Insertion Sort - O(n²) time complexity, O(1) space complexity

    Builds the final sorted array one item at a time by inserting each element
    into its correct position.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    arr = arr.copy()
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        # Move elements greater than key one position ahead
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

def merge_sort(arr: List[int]) -> List[int]:
    """
    Merge Sort - O(n log n) time complexity, O(n) space complexity

    Divides the array into halves, recursively sorts them, then merges
    the sorted halves.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    if len(arr) <= 1:
        return arr.copy()
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left: List[int], right: List[int]) -> List[int]:
    """Helper function for merge sort"""
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def quick_sort(arr: List[int]) -> List[int]:
    """
    Quick Sort - O(n log n) average, O(n²) worst case time complexity, O(log n) space complexity

    Picks a pivot element and partitions the array around it, then recursively
    sorts the sub-arrays.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    arr = arr.copy()
    _quick_sort_helper(arr, 0, len(arr) - 1)
    return arr

def _quick_sort_helper(arr: List[int], low: int, high: int) -> None:
    """Helper function for quick sort"""
    if low < high:
        pivot_idx = partition(arr, low, high)
        _quick_sort_helper(arr, low, pivot_idx - 1)
        _quick_sort_helper(arr, pivot_idx + 1, high)

def partition(arr: List[int], low: int, high: int) -> int:
    """Partition function for quick sort"""
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = (arr[j], arr[i])
    arr[i + 1], arr[high] = (arr[high], arr[i + 1])
    return i + 1

def heap_sort(arr: List[int]) -> List[int]:
    """
    Heap Sort - O(n log n) time complexity, O(1) space complexity

    Builds a max heap from the array, then repeatedly extracts the maximum
    element and places it at the end.

    Args:
        arr: List of integers to sort

    Returns:
        Sorted list
    """
    arr = arr.copy()
    n = len(arr)
    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = (arr[i], arr[0])  # Move current root to end
        heapify(arr, i, 0)  # Call heapify on reduced heap
    return arr

def heapify(arr: List[int], n: int, i: int) -> None:
    """Helper function to maintain heap property"""
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right
    if largest != i:
        arr[i], arr[largest] = (arr[largest], arr[i])
        heapify(arr, n, largest)

def counting_sort(arr: List[int]) -> List[int]:
    """
    Counting Sort - O(n + k) time complexity, O(k) space complexity
    where k is the range of input values.

    Works well when the range of potential items is not significantly greater
    than the number of items.

    Args:
        arr: List of non-negative integers to sort

    Returns:
        Sorted list
    """
    if not arr:
        return []
    # Find the range of values
    max_val = max(arr)
    min_val = min(arr)
    range_val = max_val - min_val + 1
    # Create count array
    count = [0] * range_val
    # Count occurrences
    for num in arr:
        count[num - min_val] += 1
    # Build result array
    result = []
    for i, freq in enumerate(count):
        result.extend([i + min_val] * freq)
    return result

def radix_sort(arr: List[int]) -> List[int]:
    """
    Radix Sort - O(d * (n + k)) time complexity where d is number of digits

    Sorts by processing individual digits, starting from the least significant digit.

    Args:
        arr: List of non-negative integers to sort

    Returns:
        Sorted list
    """
    if not arr:
        return []
    arr = arr.copy()
    max_val = max(arr)
    # Process each digit
    exp = 1
    while max_val // exp > 0:
        counting_sort_for_radix(arr, exp)
        exp *= 10
    return arr

def counting_sort_for_radix(arr: List[int], exp: int) -> None:
    """Helper function for radix sort"""
    n = len(arr)
    output = [0] * n
    count = [0] * 10
    # Count occurrences of each digit
    for num in arr:
        index = num // exp % 10
        count[index] += 1
    # Change count[i] to actual position
    for i in range(1, 10):
        count[i] += count[i - 1]
    # Build output array
    for i in range(n - 1, -1, -1):
        index = arr[i] // exp % 10
        output[count[index] - 1] = arr[i]
        count[index] -= 1
    # Copy output array to arr
    for i in range(n):
        arr[i] = output[i]

def bucket_sort(arr: List[float], num_buckets: int=None) -> List[float]:
    """
    Bucket Sort - O(n + k) average time complexity

    Distributes elements into buckets, sorts individual buckets, then concatenates.
    Works well for uniformly distributed data.

    Args:
        arr: List of numbers to sort
        num_buckets: Number of buckets to use

    Returns:
        Sorted list
    """
    if not arr:
        return []
    if num_buckets is None:
        num_buckets = len(arr)
    # Find range
    min_val, max_val = (min(arr), max(arr))
    bucket_range = (max_val - min_val) / num_buckets
    # Create buckets
    buckets = [[] for _ in range(num_buckets)]
    # Distribute elements into buckets
    for num in arr:
        if num == max_val:
            bucket_idx = num_buckets - 1
        else:
            bucket_idx = int((num - min_val) / bucket_range)
        buckets[bucket_idx].append(num)
    # Sort individual buckets and concatenate
    result = []
    for bucket in buckets:
        if bucket:
            bucket.sort()  # Use built-in sort for individual buckets
            result.extend(bucket)
    return result

def benchmark_sorting_algorithms():
    """Benchmark different sorting algorithms"""
    algorithms = {'Bubble Sort': bubble_sort, 'Selection Sort': selection_sort, 'Insertion Sort': insertion_sort, 'Merge Sort': merge_sort, 'Quick Sort': quick_sort, 'Heap Sort': heap_sort, 'Counting Sort': counting_sort}
    # Test with different array sizes
    sizes = [100, 500, 1000]
    for size in sizes:
        print(f"\n--- Benchmarking with array size: {size} ---")
        # Generate random array
        test_array = [random.randint(0, 1000) for _ in range(size)]
        for name, algorithm in algorithms.items():
            # Skip bubble and selection sort for larger arrays (too slow)
            if size > 500 and name in ['Bubble Sort', 'Selection Sort']:
                continue
            start_time = time.time()
            sorted_array = algorithm(test_array)
            end_time = time.time()
            # Verify correctness
            is_correct = sorted_array == sorted(test_array)
            print(f"{name:15}: {end_time - start_time:.6f}s {'✓' if is_correct else '✗'}")
if __name__ == "__main__":
    # Test all sorting algorithms
    test_array = [64, 34, 25, 12, 22, 11, 90, 5, 77, 30]
    print("Original array:", test_array)
    print("Expected sorted:", sorted(test_array))
    print()
    algorithms = {'Bubble Sort': bubble_sort, 'Selection Sort': selection_sort, 'Insertion Sort': insertion_sort, 'Merge Sort': merge_sort, 'Quick Sort': quick_sort, 'Heap Sort': heap_sort, 'Counting Sort': counting_sort, 'Radix Sort': radix_sort}
    print("Testing all sorting algorithms:")
    for name, algorithm in algorithms.items():
        result = algorithm(test_array)
        is_correct = result == sorted(test_array)
        print(f"{name:15}: {result} {'✓' if is_correct else '✗'}")
    # Test bucket sort with floats
    float_array = [0.78, 0.17, 0.39, 0.26, 0.72, 0.94, 0.21, 0.12, 0.23, 0.68]
    print(f"\nBucket Sort (floats): {bucket_sort(float_array)}")
    # Run benchmarks
    print("\n" + "=" * 50)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 50)
    benchmark_sorting_algorithms()