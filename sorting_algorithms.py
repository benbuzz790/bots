def bubble_sort(arr):
    """
    Sort an array using bubble sort algorithm.
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
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


def selection_sort(arr):
    """
    Sort an array using selection sort algorithm.
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
    """
    arr = arr.copy()
    n = len(arr)

    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]

    return arr


def insertion_sort(arr):
    """
    Sort an array using insertion sort algorithm.
    Time Complexity: O(n²)
    Space Complexity: O(1)

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
    """
    arr = arr.copy()

    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

    return arr


def merge_sort(arr):
    """
    Sort an array using merge sort algorithm.
    Time Complexity: O(n log n)
    Space Complexity: O(n)

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)


def merge(left, right):
    """Helper function for merge sort."""
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


def quick_sort(arr):
    """
    Sort an array using quick sort algorithm.
    Time Complexity: O(n log n) average, O(n²) worst
    Space Complexity: O(log n)

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quick_sort(left) + middle + quick_sort(right)


if __name__ == "__main__":
    # Test all sorting algorithms
    test_arrays = [[64, 34, 25, 12, 22, 11, 90], [5, 2, 8, 1, 9], [1], [], [3, 3, 3, 3], [9, 8, 7, 6, 5, 4, 3, 2, 1]]

    algorithms = [
        ("Bubble Sort", bubble_sort),
        ("Selection Sort", selection_sort),
        ("Insertion Sort", insertion_sort),
        ("Merge Sort", merge_sort),
        ("Quick Sort", quick_sort),
    ]

    for test_arr in test_arrays:
        print(f"\nOriginal: {test_arr}")
        for name, func in algorithms:
            sorted_arr = func(test_arr)
            print(f"{name:15} -> {sorted_arr}")
