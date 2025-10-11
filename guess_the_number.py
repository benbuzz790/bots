"""
Guess the Number Game
A simple interactive game where the player tries to guess a random number.
"""

import random


def guess_the_number():
    """Main game function for Guess the Number."""
    print("=" * 50)
    print("Welcome to Guess the Number!")
    print("=" * 50)

    # Game settings
    min_number = 1
    max_number = 100
    max_attempts = 7

    # Generate random number
    secret_number = random.randint(min_number, max_number)
    attempts = 0

    print(f"\nI'm thinking of a number between {min_number} and {max_number}.")
    print(f"You have {max_attempts} attempts to guess it!\n")

    while attempts < max_attempts:
        try:
            guess = int(input(f"Attempt {attempts + 1}/{max_attempts} - Enter your guess: "))
            attempts += 1

            if guess < min_number or guess > max_number:
                print(f"Please guess a number between {min_number} and {max_number}!")
                continue

            if guess < secret_number:
                print("📈 Too low! Try a higher number.\n")
            elif guess > secret_number:
                print("📉 Too high! Try a lower number.\n")
            else:
                print(f"\n🎉 Congratulations! You guessed it in {attempts} attempts!")
                print(f"The number was {secret_number}!")
                return True

        except ValueError:
            print("Invalid input! Please enter a number.\n")

    print(f"\n😔 Game Over! You've used all {max_attempts} attempts.")
    print(f"The secret number was {secret_number}.")
    return False


def main():
    """Main function to run the game with replay option."""
    while True:
        guess_the_number()

        play_again = input("\nWould you like to play again? (yes/no): ").lower()
        if play_again not in ["yes", "y"]:
            print("\nThanks for playing! Goodbye! 👋")
            break
        print("\n")


if __name__ == "__main__":
    main()
