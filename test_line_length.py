"""
Test file to check line length enforcement in the CI/CD pipeline.
This file contains lines of various lengths to identify which tool enforces 79 chars.
"""

def short_function():
    """This is a short line."""
    return "short"

def medium_length_function_with_a_longer_name_that_goes_beyond_seventy_nine_characters():
    """This line is exactly 80 characters long and should trigger 79-char limit."""
    return "medium"

def very_long_function_name_that_definitely_exceeds_seventy_nine_characters_and_approaches_one_hundred_twenty_seven():
    """This line is around 120+ characters and should be fine with 127-char limit but fail with 79-char limit."""
    very_long_variable_name_that_makes_this_line_exceed_seventy_nine_characters = "test"
    another_very_long_line_that_should_definitely_trigger_any_seventy_nine_character_limit_enforcement = "fail"
    return very_long_variable_name_that_makes_this_line_exceed_seventy_nine_characters + another_very_long_line_that_should_definitely_trigger_any_seventy_nine_character_limit_enforcement
# This comment is designed to be exactly 80 characters long to test limits
# This comment is much longer and should definitely exceed the 79 character limit that some tools might enforce in the pipeline