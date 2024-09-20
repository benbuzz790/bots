import re
import string
import random
from typing import List, Tuple
from contextlib import contextmanager
from io import StringIO
import sys
import time

def count_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a given text.
    This is a rough estimation and may not be accurate for all models.
    """
    return len(re.findall(r'\w+', text))

@contextmanager
def captured_output():
    """
    Context manager to capture stdout and stderr
    """
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length"""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def generate_test_cases() -> List[Tuple[str, str]]:
    """Generate a list of test cases for factual accuracy testing"""
    return [
        ("What is the capital of France?", "Paris"),
        ("Who wrote 'To Kill a Mockingbird'?", "Harper Lee"),
        ("What's the square root of 144?", "12"),
        ("In which year did World War II end?", "1945"),
        ("What's the chemical symbol for gold?", "Au"),
    ]

def measure_time(func):
    """Decorator to measure the execution time of a function"""
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds to execute.")
        return result
    return wrapper

def retry(exceptions, tries=3, delay=1, backoff=2):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"Exception: {e}, Retrying in {mdelay} seconds...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

def assert_response_quality(response: str, min_length: int = 50, max_length: int = 1000):
    """Assert that the response meets basic quality criteria"""
    assert isinstance(response, str), "Response should be a string"
    assert min_length <= len(response) <= max_length, f"Response length should be between {min_length} and {max_length}"
    assert not response.isspace(), "Response should not be empty or only whitespace"

# You can add more utility functions here as needed for your tests