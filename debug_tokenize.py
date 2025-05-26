import ast

def debug_insert_after_issue():
    """Debug the insert_after issue with comments"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    content = 'import os\nfrom typing import List, Optional\n\ndef outer_func():\n    def inner_func():\n        pass\n    return inner_func\n\nclass OuterClass:\n    def method(self):\n        pass\n\n    class InnerClass:\n        @staticmethod\n        def static_method():\n            pass\n\n        async def async_method(self):\n            pass\n\n    def another_method(self):\n        # Insert here\n        pass\n'
    print('=== ORIGINAL CONTENT ===')
    print(repr(content))
    print('\n=== TOKENIZATION ===')
    tokenized, token_map = _tokenize_source(content)
    print('Tokenized:')
    print(repr(tokenized))
    print('\nToken map:')
    for k, v in token_map.items():
        print(f'  {k}: {repr(v)}')
    print('\n=== DETOKENIZATION ===')
    restored = _detokenize_source(tokenized, token_map)
    print('Restored:')
    print(repr(restored))
    print('\n=== COMPARISON ===')
    print(f'Original == Restored: {content == restored}')
    if '# Insert here' in content:
        print(f'Comment in original: True')
    if '# Insert here' in restored:
        print(f'Comment in restored: True')
    else:
        print(f'Comment in restored: False')
        for k, v in token_map.items():
            if 'Insert here' in v:
                print(f'Comment found in token: {k} -> {repr(v)}')
                if k in restored:
                    print(f'Token found in restored content')
                else:
                    print(f'Token NOT found in restored content')
if __name__ == '__main__':
    debug_insert_after_issue()

def debug_line_matching():
    """Debug how line matching works in the insertion logic"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    import ast
    content = 'def another_method(self):\n        # Insert here\n        pass'
    print('=== ORIGINAL CONTENT ===')
    print(repr(content))
    tokenized, token_map = _tokenize_source(content)
    print('\n=== TOKENIZED ===')
    print(repr(tokenized))
    tree = ast.parse(tokenized)
    func_node = tree.body[0]
    print(f'\nFunction spans lines {func_node.lineno} to {func_node.end_lineno}')
    file_lines = tokenized.split('\n')
    print(f'\nFile lines: {file_lines}')
    func_lines = file_lines[func_node.lineno - 1:func_node.end_lineno]
    print(f'\nFunction lines: {func_lines}')
    target = '# Insert here'
    print(f'\nLooking for target: {repr(target)}')
    for i, line in enumerate(func_lines):
        print(f'Line {i}: {repr(line)}')
        detokenized_line = _detokenize_source(line, token_map)
        print(f'  Detokenized: {repr(detokenized_line)}')
        print(f'  Stripped: {repr(detokenized_line.strip())}')
        print(f'  Target match: {detokenized_line.strip() == target}')
if __name__ == '__main__':
    debug_line_matching()

def debug_ast_comment_loss():
    """Debug why comments are lost during AST processing"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    from bots.utils.helpers import _py_ast_to_source
    import ast
    content = 'def another_method(self):\n        # Insert here\n        pass'
    print('=== ORIGINAL ===')
    print(repr(content))
    print('\n=== TOKENIZED ===')
    tokenized, token_map = _tokenize_source(content)
    print(repr(tokenized))
    print('Token map:', token_map)
    print('\n=== AST PARSE ===')
    tree = ast.parse(tokenized)
    print('AST body:', [type(node).__name__ for node in tree.body])
    func_node = tree.body[0]
    print('Function body:', [type(node).__name__ for node in func_node.body])
    print('\n=== AST UNPARSE ===')
    unparsed = _py_ast_to_source(tree)
    print(repr(unparsed))
    print('\n=== DETOKENIZED ===')
    final = _detokenize_source(unparsed, token_map)
    print(repr(final))
if __name__ == '__main__':
    debug_ast_comment_loss()

def debug_string_literal_unparsing():
    """Debug how AST handles our string literals"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    from bots.utils.helpers import _py_ast_to_source
    import ast
    content = 'def test_func():\n        x = 1\n        # marker\n        z = 3'
    print('=== ORIGINAL ===')
    print(repr(content))
    print('\n=== TOKENIZED ===')
    tokenized, token_map = _tokenize_source(content)
    print(repr(tokenized))
    print('Token map:', token_map)
    print('\n=== AST PARSE ===')
    tree = ast.parse(tokenized)
    func_node = tree.body[0]
    print('Function body nodes:')
    for i, node in enumerate(func_node.body):
        print(f'  {i}: {type(node).__name__}')
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            print(f'     Constant value: {repr(node.value.value)}')
    print('\n=== AST UNPARSE ===')
    unparsed = _py_ast_to_source(tree)
    print(repr(unparsed))
    print('\n=== DETOKENIZED ===')
    final = _detokenize_source(unparsed, token_map)
    print(repr(final))
if __name__ == '__main__':
    debug_string_literal_unparsing()

def debug_inline_comments():
    """Debug inline comment tokenization"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    import ast
    content = 'def func():\n        x = 1  # comment one\n        # standalone comment\n        y = 2  # comment two'
    print('=== ORIGINAL ===')
    print(repr(content))
    print('\n=== TOKENIZED ===')
    try:
        tokenized, token_map = _tokenize_source(content)
        print(repr(tokenized))
        print('Token map:', token_map)
        print('\n=== AST PARSE TEST ===')
        try:
            tree = ast.parse(tokenized)
            print('AST parsing successful')
        except Exception as e:
            print(f'AST parsing failed: {e}')
            lines = tokenized.split('\n')
            for i, line in enumerate(lines, 1):
                print(f'Line {i}: {repr(line)}')
    except Exception as e:
        print(f'Tokenization failed: {e}')
if __name__ == '__main__':
    debug_inline_comments()

def debug_complete_inline_flow():
    """Debug the complete inline comment flow"""
    from bots.tools.python_edit import _tokenize_source, _detokenize_source
    from bots.utils.helpers import _py_ast_to_source
    import ast
    content = 'def func():\n        x = 1  # comment one\n        # standalone comment\n        y = 2  # comment two'
    print('=== ORIGINAL ===')
    print(repr(content))
    print('\n=== TOKENIZED ===')
    tokenized, token_map = _tokenize_source(content)
    print(repr(tokenized))
    print('\n=== AST PARSE & UNPARSE ===')
    tree = ast.parse(tokenized)
    unparsed = _py_ast_to_source(tree)
    print(repr(unparsed))
    print('\n=== DETOKENIZED ===')
    final = _detokenize_source(unparsed, token_map)
    print(repr(final))
    print(f'\n=== COMPARISON ===')
    print(f'Original == Final: {content == final}')
if __name__ == '__main__':
    debug_complete_inline_flow()