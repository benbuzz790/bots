def greet(name):
    """
    A simple function that greets a person by name.

    Args:
        name (str): The name of the person to greet

    Returns:
        str: A greeting message
    """
    return f"Hello, {name}! Welcome!"


def calculate_sum(a, b):
    """
    A simple function that adds two numbers together.

    Args:
        a (int/float): First number
        b (int/float): Second number

    Returns:
        int/float: The sum of a and b
    """
    return a + b


# Example usage
if __name__ == "__main__":
    print(greet("Alice"))
    print(calculate_sum(5, 3))
