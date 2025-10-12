"""
Sorting algorithms implementation
"""


def quicksort(arr):
    """
    QuickSort algorithm implementation.

    Time Complexity: O(n log n) average, O(n²) worst case
    Space Complexity: O(log n) due to recursion

    Args:
        arr: List of comparable elements to sort

    Returns:
        Sorted list in ascending order
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)


def bubble_sort(arr):
    """
    Bubble Sort algorithm implementation.

    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr: List of comparable elements to sort

    Returns:
        Sorted list in ascending order
    """
    arr = arr.copy()  # Don't modify original
    n = len(arr)

    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break

    return arr


def merge_sort(arr):
    """
    Merge Sort algorithm implementation.

    Time Complexity: O(n log n)
    Space Complexity: O(n)

    Args:
        arr: List of comparable elements to sort

    Returns:
        Sorted list in ascending order
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)


def merge(left, right):
    """Helper function for merge_sort"""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result


if __name__ == "__main__":
    # Example usage
    test_array = [64, 34, 25, 12, 22, 11, 90]

    print("Original array:", test_array)
    print("QuickSort:", quicksort(test_array))
    print("Bubble Sort:", bubble_sort(test_array))
    print("Merge Sort:", merge_sort(test_array))
