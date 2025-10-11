def quicksort(arr):
    """
    Sort an array using the QuickSort algorithm.

    Parameters:
    -----------
    arr : list
        The list to be sorted

    Returns:
    --------
    list
        A new sorted list (original list is not modified)

    Examples:
    ---------
    >>> quicksort([3, 6, 8, 10, 1, 2, 1])
    [1, 1, 2, 3, 6, 8, 10]
    >>> quicksort([5, 4, 3, 2, 1])
    [1, 2, 3, 4, 5]
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
    Sort an array using the Bubble Sort algorithm (in-place).

    Parameters:
    -----------
    arr : list
        The list to be sorted

    Returns:
    --------
    list
        The sorted list (modifies original)
    """
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


# Example usage
if __name__ == "__main__":
    test_array = [64, 34, 25, 12, 22, 11, 90]

    print("Original array:", test_array)
    print("QuickSort result:", quicksort(test_array))

    test_array2 = [64, 34, 25, 12, 22, 11, 90]
    print("Bubble Sort result:", bubble_sort(test_array2))
