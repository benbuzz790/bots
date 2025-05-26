# Test the tokenization functions in isolation
from bots.tools.python_edit import _tokenize_source, _detokenize_source

# Start with the simplest failing case
problematic_source = '''def example():
    """
    Multiline
    docstring
    """
    # Comment
    pass'''

print("Testing tokenization...")
try:
    tokenized, token_map = _tokenize_source(problematic_source)
    print("Tokenization successful")
    print("Testing detokenization...")
    restored = _detokenize_source(tokenized, token_map)
    print("Detokenization successful")
except Exception as e:
    print(f"Error: {e}")