#!/usr/bin/env python3
"""
A simple greeting program with multiple functions.
"""


def greet(name):
    """Return a personalized greeting."""
    return f"Hello, {name}! Welcome to Python programming!"


def farewell(name):
    """Return a personalized farewell message."""
    return f"Goodbye, {name}! Have a great day!"


def main():
    """Main function to run the program."""
    user_name = input("What's your name? ")
    print(greet(user_name))
    print(farewell(user_name))


if __name__ == "__main__":
    main()
