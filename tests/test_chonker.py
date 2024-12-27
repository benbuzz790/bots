"""
Test cases demonstrating the chunking algorithm's behavior under various scenarios:
1. Initial chunking of realistic code
2. Small edits and their effects on chunks
3. Large edits (3000+ chars) and their impact
"""

import textwrap
from bots.tools._chonker import chunk_python_code_all_properties

def print_chunking_comparison(before_code: str, after_code: str, description: str):
    """Helper to show how chunking changes between two versions of code"""
    print("=" * 80)
    print(f"TEST: {description}")
    print("-" * 40)
    print("BEFORE CHUNKING:")
    print(chunk_python_code_all_properties(before_code))
    print("\nAFTER CHUNKING:")
    print(chunk_python_code_all_properties(after_code))
    print("=" * 80)
    print()

def test_initial_chunking():
    """Test 1: How does it chunk realistic code?"""
    code = textwrap.dedent("""
        class DataProcessor:
            def __init__(self, data_source):
                self.data_source = data_source
                self.processed = False
                
            def process_data(self):
                # First stage processing
                results = []
                for item in self.data_source:
                    if isinstance(item, dict):
                        results.append(self._process_dict(item))
                    else:
                        results.append(self._process_item(item))
                self.processed = True
                return results
                
            def _process_dict(self, item):
                return {k: v.strip() if isinstance(v, str) else v 
                        for k, v in item.items()}
                
            def _process_item(self, item):
                return str(item).strip()
    """)
    
    print("Test 1: Initial chunking of realistic code")
    print(chunk_python_code_all_properties(code))
    print("\n")

def test_small_edits():
    """Test 2: How do small edits affect chunking?"""
    before_code = textwrap.dedent("""
        def calculate_stats(data):
            total = sum(data)
            avg = total / len(data)
            return {
                'total': total,
                'average': avg
            }
    """)

    # Small edit: Add one line
    after_code_1 = textwrap.dedent("""
        def calculate_stats(data):
            total = sum(data)
            avg = total / len(data)
            max_val = max(data)  # Added line
            return {
                'total': total,
                'average': avg
            }
    """)

    # Small edit: Change variable names
    after_code_2 = textwrap.dedent("""
        def calculate_stats(numbers):  # Changed parameter name
            sum_total = sum(numbers)   # Changed variable name
            average = sum_total / len(numbers)  # Changed names
            return {
                'total': sum_total,
                'average': average
            }
    """)

    print_chunking_comparison(before_code, after_code_1, 
                            "Small edit - adding one line")
    print_chunking_comparison(before_code, after_code_2,
                            "Small edit - renaming variables")

def test_large_edits():
    """Test 3: How do large edits affect chunking?"""
    before_code = textwrap.dedent("""
        def process_data(items):
            results = []
            for item in items:
                results.append(item * 2)
            return results
    """)

    # Add a large docstring (about 3000 chars)
    large_docstring = '"""' + 'x' * 3000 + '"""'
    after_code_1 = textwrap.dedent(f"""
        def process_data(items):
            {large_docstring}
            results = []
            for item in items:
                results.append(item * 2)
            return results
    """)

    # Add a large function (lots of similar lines)
    many_lines = "\n".join(f"    result.append(process_{i}(item))"
                          for i in range(100))
    after_code_2 = textwrap.dedent(f"""
        def process_data(items):
            results = []
            for item in items:
                results.append(item * 2)
            return results

        def process_large_dataset(items):
            result = []
            {many_lines}
            return result
    """)

    print_chunking_comparison(before_code, after_code_1,
                            "Large edit - adding 3000 char docstring")
    print_chunking_comparison(before_code, after_code_2,
                            "Large edit - adding function with 100 similar lines")

def main():
    """Run all tests"""
    test_initial_chunking()
    test_small_edits()
    test_large_edits()

if __name__ == "__main__":
    main()