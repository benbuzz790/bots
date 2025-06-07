"""
Sorting Algorithms Module

This module contains implementations of various sorting algorithms
including bubble sort, selection sort, insertion sort, merge sort,
quick sort, and heap sort.
"""

def bubble_sort(arr):
    """
    Bubble Sort Algorithm
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
    """
    arr = arr.copy()  # Don't modify original array
    n = len(arr)
    for i in range(n):
        # Flag to optimize - if no swaps occur, array is sorted
        swapped = False
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = (arr[j + 1], arr[j])
                swapped = True
        # If no swapping occurred, array is sorted
        if not swapped:
            break
    return arr

def selection_sort(arr):
    """
    Selection Sort Algorithm
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
    """
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        # Find the minimum element in remaining unsorted array
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        # Swap the found minimum element with the first element
        arr[i], arr[min_idx] = (arr[min_idx], arr[i])
    return arr

def insertion_sort(arr):
    """
    Insertion Sort Algorithm
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
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

def merge_sort(arr):
    """
    Merge Sort Algorithm
    Time Complexity: O(n log n)
    Space Complexity: O(n)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
    """
    if len(arr) <= 1:
        return arr.copy()
    # Divide the array into two halves
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    # Merge the sorted halves
    return merge(left, right)

def merge(left, right):
    """
    Helper function for merge sort to merge two sorted arrays

    Args:
        left: Left sorted array
        right: Right sorted array

    Returns:
        List: Merged sorted array
    """
    result = []
    i = j = 0
    # Compare elements and merge in sorted order
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

def quick_sort(arr):
    """
    Quick Sort Algorithm
    Time Complexity: O(n log n) average, O(n²) worst case
    Space Complexity: O(log n)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
    """
    if len(arr) <= 1:
        return arr.copy()
    arr = arr.copy()
    _quick_sort_helper(arr, 0, len(arr) - 1)
    return arr

def _quick_sort_helper(arr, low, high):
    """
    Helper function for quick sort

    Args:
        arr: Array to sort
        low: Starting index
        high: Ending index
    """
    if low < high:
        # Partition the array and get pivot index
        pivot_idx = partition(arr, low, high)
        # Recursively sort elements before and after partition
        _quick_sort_helper(arr, low, pivot_idx - 1)
        _quick_sort_helper(arr, pivot_idx + 1, high)

def partition(arr, low, high):
    """
    Partition function for quick sort using last element as pivot

    Args:
        arr: Array to partition
        low: Starting index
        high: Ending index

    Returns:
        int: Final position of pivot
    """
    pivot = arr[high]  # Choose last element as pivot
    i = low - 1  # Index of smaller element
    for j in range(low, high):
        # If current element is smaller than or equal to pivot
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = (arr[j], arr[i])
    arr[i + 1], arr[high] = (arr[high], arr[i + 1])
    return i + 1

def heap_sort(arr):
    """
    Heap Sort Algorithm
    Time Complexity: O(n log n)
    Space Complexity: O(1)

    Args:
        arr: List of comparable elements

    Returns:
        List: Sorted list in ascending order
    """
    arr = arr.copy()
    n = len(arr)
    # Build a max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        # Move current root to end
        arr[0], arr[i] = (arr[i], arr[0])
        # Call heapify on the reduced heap
        heapify(arr, i, 0)
    return arr

def heapify(arr, n, i):
    """
    Helper function to maintain heap property

    Args:
        arr: Array to heapify
        n: Size of heap
        i: Root index
    """
    largest = i  # Initialize largest as root
    left = 2 * i + 1  # Left child
    right = 2 * i + 2  # Right child
    # Check if left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left
    # Check if right child exists and is greater than largest so far
    if right < n and arr[right] > arr[largest]:
        largest = right
    # Change root if needed
    if largest != i:
        arr[i], arr[largest] = (arr[largest], arr[i])
        # Heapify the root
        heapify(arr, n, largest)

def counting_sort(arr, max_val=None):
    """
    Counting Sort Algorithm (for non-negative integers)
    Time Complexity: O(n + k) where k is the range of input
    Space Complexity: O(k)

    Args:
        arr: List of non-negative integers
        max_val: Maximum value in array (optional, will be computed if not provided)

    Returns:
        List: Sorted list in ascending order
    """
    if not arr:
        return []
    if max_val is None:
        max_val = max(arr)
    # Create count array
    count = [0] * (max_val + 1)
    # Count occurrences of each element
    for num in arr:
        count[num] += 1
    # Build the sorted array
    result = []
    for i in range(len(count)):
        result.extend([i] * count[i])
    return result
# Demonstration and testing functions

def compare_sorting_algorithms(arr):
    """
    Compare different sorting algorithms on the same array

    Args:
        arr: List to sort

    Returns:
        dict: Results from different sorting algorithms
    """
    import time
    algorithms = {'Bubble Sort': bubble_sort, 'Selection Sort': selection_sort, 'Insertion Sort': insertion_sort, 'Merge Sort': merge_sort, 'Quick Sort': quick_sort, 'Heap Sort': heap_sort}
    results = {}
    for name, func in algorithms.items():
        start_time = time.time()
        sorted_arr = func(arr)
        end_time = time.time()
        results[name] = {'sorted_array': sorted_arr, 'time_taken': end_time - start_time, 'is_sorted': sorted_arr == sorted(arr)}
    return results
if __name__ == "__main__":
    # Example usage
    test_array = [64, 34, 25, 12, 22, 11, 90, 88, 76, 50, 42]
    print(f"Original array: {test_array}")
    print()
    # Test each sorting algorithm
    print("Bubble Sort:", bubble_sort(test_array))
    print("Selection Sort:", selection_sort(test_array))
    print("Insertion Sort:", insertion_sort(test_array))
    print("Merge Sort:", merge_sort(test_array))
    print("Quick Sort:", quick_sort(test_array))
    print("Heap Sort:", heap_sort(test_array))
    print("Counting Sort:", counting_sort(test_array))
    print()
    # Performance comparison
    print("Performance Comparison:")
    results = compare_sorting_algorithms(test_array)
    for name, result in results.items():
        print(f"{name}: {result['time_taken']:.6f} seconds - Correct: {result['is_sorted']}")