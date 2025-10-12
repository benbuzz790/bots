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
    """
    Helper function to merge two sorted arrays.

    Args:
        left (list): First sorted list
        right (list): Second sorted list

    Returns:
        list: Merged sorted list
    """
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
