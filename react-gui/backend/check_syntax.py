import ast

try:
    with open('bot_manager.py', 'r') as f:
        content = f.read()
    ast.parse(content)
    print('✅ Syntax OK')
except SyntaxError as e:
    print(f'❌ Syntax Error: {e}')
    print(f'Line {e.lineno}: {e.text}')
except Exception as e:
    print(f'❌ Other error: {e}')
