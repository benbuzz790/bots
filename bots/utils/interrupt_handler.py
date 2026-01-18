"""Interrupt handling utilities for making blocking operations interruptible.

This module provides utilities to make blocking operations (like API calls)
interruptible with Ctrl-C (KeyboardInterrupt).
"""

import threading
from typing import Callable, TypeVar

T = TypeVar("T")


class InterruptibleOperation:
    """Wrapper to make blocking operations interruptible with Ctrl-C."""

    def __init__(self, check_interval: float = 0.1):
        """Initialize the interruptible operation handler.

        Args:
            check_interval: How often to check for interrupts (in seconds)
        """
        self.check_interval = check_interval
        self._interrupted = False
        self._result = None
        self._exception = None
        self._thread = None

    def run(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Run a function in a way that can be interrupted with Ctrl-C.

        Args:
            func: The function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function

        Raises:
            KeyboardInterrupt: If Ctrl-C is pressed during execution
            Exception: Any exception raised by the function
        """
        self._result = None
        self._exception = None
        self._interrupted = False

        # Run the function in a separate thread
        def target():
            try:
                self._result = func(*args, **kwargs)
            except Exception as e:
                self._exception = e

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

        # Wait for completion, checking for interrupts periodically
        while self._thread.is_alive():
            try:
                self._thread.join(timeout=self.check_interval)
            except KeyboardInterrupt:
                # Ctrl-C was pressed
                self._interrupted = True
                # Give the thread a moment to finish if it's close
                self._thread.join(timeout=0.5)
                raise KeyboardInterrupt("Operation interrupted by user")

        # Check if an exception occurred in the thread
        if self._exception:
            raise self._exception

        return self._result


def make_interruptible(func: Callable[..., T], check_interval: float = 0.1) -> Callable[..., T]:
    """Decorator to make a function interruptible with Ctrl-C.

    Args:
        func: The function to make interruptible
        check_interval: How often to check for interrupts (in seconds)

    Returns:
        A wrapped version of the function that can be interrupted

    Example:
        @make_interruptible
        def long_running_operation():
            # This can now be interrupted with Ctrl-C
            return api_call()
    """

    def wrapper(*args, **kwargs) -> T:
        handler = InterruptibleOperation(check_interval=check_interval)
        return handler.run(func, *args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def run_interruptible(func: Callable[..., T], *args, check_interval: float = 0.1, **kwargs) -> T:
    """Run a function in an interruptible way.

    This is a convenience function that creates an InterruptibleOperation
    and runs the function.

    Args:
        func: The function to run
        *args: Positional arguments for the function
        check_interval: How often to check for interrupts (in seconds)
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function

    Raises:
        KeyboardInterrupt: If Ctrl-C is pressed during execution
        Exception: Any exception raised by the function

    Example:
        result = run_interruptible(bot.respond, "Hello", check_interval=0.1)
    """
    handler = InterruptibleOperation(check_interval=check_interval)
    return handler.run(func, *args, **kwargs)
