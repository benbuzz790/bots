from bots.tools.python_edit import tokenize_source
import time
source = '''
    # Header comment
    x = "string literal"  # Inline comment
    y = 1
    '''
print("Starting tokenization...")
start = time.time()
try:
    tokenized, token_map = tokenize_source(source)
    end = time.time()
    print(f"Success! Time: {end - start:.6f} seconds")
    print(f"Tokenized: {repr(tokenized[:100])}")
    print(f"Token map: {token_map}")
except Exception as e:
    end = time.time()
    print(f"Error after {end - start:.6f} seconds: {e}")
    import traceback
    traceback.print_exc()
