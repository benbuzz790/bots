import re
import time
# Test the regex patterns
test_string = '    x = "string literal"  # Inline comment'
patterns = [
    r'"[^"\\]*(?:\\.[^"\\]*)*"',  # Current pattern
    r'"(?:[^"\\]|\\.)*"',          # Alternative 1
    r'"[^"]*"',                    # Simple pattern
]
for i, pattern in enumerate(patterns):
    print(f"\nTesting pattern {i+1}: {pattern}")
    start = time.time()
    try:
        match = re.search(pattern, test_string)
        end = time.time()
        if match:
            print(f"  Match found: {match.group()}")
        else:
            print("  No match")
        print(f"  Time: {end - start:.6f} seconds")
    except Exception as e:
        print(f"  Error: {e}")
# Test with the actual problematic input
source = '\n    # Header comment\n    x = "string literal"  # Inline comment\n    y = 1\n    '
print(f"\n\nTesting with actual source:")
print(f"Source: {repr(source)}")
# Split into lines like the actual code does
lines = source.split('\n')
for i, line in enumerate(lines):
    if not line.strip():
        continue
    print(f"\nLine {i}: {repr(line)}")
    indent = len(line) - len(line.lstrip())
    content = line[indent:]
    print(f"  Content: {repr(content)}")
    # Test the pattern
    pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"'
    start = time.time()
    try:
        match = re.search(pattern, content)
        end = time.time()
        if match:
            print(f"  Match: {match.group()}")
        print(f"  Time: {end - start:.6f} seconds")
    except Exception as e:
        print(f"  Error: {e}")
