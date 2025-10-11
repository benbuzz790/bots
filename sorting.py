def bubble_sort(arr):
    """
    Sort an array using bubble sort algorithm.

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


def quick_sort(arr):
    """
    Sort an array using quick sort algorithm.

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


def merge_sort(arr):
    """
    Sort an array using merge sort algorithm.

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


def insertion_sort(arr):
    """
    Sort an array using insertion sort algorithm.

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


def selection_sort(arr):
    """
    Sort an array using selection sort algorithm.

    Args:
        arr (list): List to be sorted

    Returns:
        list: Sorted list
    """
    arr = arr.copy()

    for i in range(len(arr)):
        min_idx = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]

    return arr


# Example usage
if __name__ == "__main__":
    test_array = [64, 34, 25, 12, 22, 11, 90]

    print("Original array:", test_array)
    print("\nBubble Sort:", bubble_sort(test_array))
    print("Quick Sort:", quick_sort(test_array))
    print("Merge Sort:", merge_sort(test_array))
    print("Insertion Sort:", insertion_sort(test_array))
    print("Selection Sort:", selection_sort(test_array))
