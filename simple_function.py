def calculate_average(numbers):
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: A list of numbers

    Returns:
        The average of the numbers, or None if the list is empty
    """
    if not numbers:
        return None

    return sum(numbers) / len(numbers)


# Example usage
if __name__ == "__main__":
    test_numbers = [10, 20, 30, 40, 50]
    result = calculate_average(test_numbers)
    print(f"The average of {test_numbers} is {result}")
