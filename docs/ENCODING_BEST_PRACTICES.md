# Encoding Best Practices for GitHub Docs App

## Overview

This document outlines best practices for handling unicode and encoding in the GitHub Docs App to prevent mojibake and encoding issues.

## Background

**Mojibake** (文字化け) occurs when text is encoded in one character encoding but decoded using a different encoding. For example:
- ✅ (checkmark emoji) displayed as `Γ£à` when UTF-8 is decoded as CP437
- This commonly happens with PowerShell on Windows, which defaults to CP437 encoding

## Core Principles

### 1. Always Use UTF-8 Encoding

**DO:**
```python
# File operations
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Writing files
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**DON'T:**
```python
# Without explicit encoding (uses system default)
with open(file_path, 'r') as f:  # ❌ BAD
    content = f.read()
```

### 2. PowerShell Subprocess Calls

**DO:**
```python
import subprocess

# CORRECT: With UTF-8 encoding
result = subprocess.run(
    ['powershell', '-Command',
     '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; ' + command],
    capture_output=True,
    encoding='utf-8',
    errors='replace'
)
```

**DON'T:**
```python
# INCORRECT: Without UTF-8 encoding (causes mojibake)
result = subprocess.run(
    ['powershell', '-Command', command],  # ❌ BAD
    capture_output=True,
    text=True
)
```

### 3. Git Operations

**DO:**
```python
# Git commit messages with emoji
commit_msg = "Add feature ✅"
repo.index.commit(commit_msg)  # Git handles UTF-8 by default

# Reading git output
log_output = repo.git.log('--oneline', encoding='utf-8')
```

**DON'T:**
```python
# Assuming ASCII-only commit messages
commit_msg = "Add feature"  # ❌ Limited, not future-proof
```

### 4. Console Output and Logging

**DO:**
```python
import logging

# Logging with unicode
logger.info(f"Task completed ✅")
print(f"Status: {emoji} | Progress: {percent}%")

# JSON output
import json
data = {"status": "✅", "message": "中文"}
json_str = json.dumps(data, ensure_ascii=False)  # Preserve unicode
```

**DON'T:**
```python
# ASCII-only JSON
json_str = json.dumps(data, ensure_ascii=True)  # ❌ Escapes unicode
```

## Common Pitfalls

### 1. Windows PowerShell Default Encoding

**Problem:** PowerShell on Windows defaults to CP437 (DOS) encoding, not UTF-8.

**Solution:** Always prefix PowerShell commands with UTF-8 encoding setup:
```python
utf8_prefix = '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; '
command = utf8_prefix + your_command
```

### 2. File Path Encoding

**Problem:** File paths with unicode characters may not work on all systems.

**Solution:**
```python
from pathlib import Path

# Use Path objects which handle encoding properly
file_path = Path("测试文件.txt")
file_path.write_text(content, encoding='utf-8')
```

### 3. Environment Variables

**Problem:** Environment variables may contain unicode that gets mangled.

**Solution:**
```python
import os

# Read with proper encoding
value = os.environ.get('VAR_NAME', '')
# On Windows, may need to decode from system encoding
if sys.platform == 'win32':
    value = value.encode('latin-1').decode('utf-8', errors='replace')
```

### 4. Database Storage

**Problem:** Database may not store unicode correctly.

**Solution:**
```python
# Ensure database connection uses UTF-8
# For SQLite
conn = sqlite3.connect('db.sqlite3')
conn.execute('PRAGMA encoding = "UTF-8"')

# For PostgreSQL (usually UTF-8 by default)
# Verify with: SHOW SERVER_ENCODING;
```

## Testing Strategy

### Test Categories

1. **PowerShell Subprocess Tests** (`test_subprocess_encoding.py`)
   - Verify UTF-8 encoding prefix works
   - Test that omitting UTF-8 causes mojibake
   - Test error handling with unicode

2. **File I/O Tests** (`test_file_io_unicode.py`)
   - Read/write files with unicode content
   - Unicode filenames
   - Different encodings (utf-8, utf-16, latin-1)
   - Malformed unicode handling

3. **Git Operations Tests** (`test_git_unicode.py`)
   - Commit messages with emoji
   - Git log parsing with unicode
   - File content with unicode

4. **Console Output Tests** (`test_console_encoding.py`)
   - Logging with unicode
   - Progress indicators with emoji
   - Error messages with unicode

### Running Tests

```bash
# Run all encoding tests
pytest tests/test_*encoding*.py tests/test_*unicode*.py -v

# Run specific test category
pytest tests/test_subprocess_encoding.py -v

# Run with coverage
pytest tests/test_*encoding*.py --cov=src --cov-report=html
```

## Unicode Test Characters

Use these standard test characters from `tests/encoding_fixtures.py`:

```python
UNICODE_TEST_STRINGS = {
    'emoji_checkmark': '✅',
    'emoji_cross': '❌',
    'emoji_warning': '⚠️',
    'emoji_party': '🎉',
    'emoji_memo': '📝',
    'emoji_wrench': '🔧',
    'chinese': '中文测试',
    'arabic': 'العربية',
    'mixed': '✅ Test 中文 🎉 العربية ❌',
}
```

## Debugging Encoding Issues

### 1. Identify the Problem

```python
# Check what encoding is being used
import sys
print(f"Default encoding: {sys.getdefaultencoding()}")
print(f"Filesystem encoding: {sys.getfilesystemencoding()}")
print(f"Stdout encoding: {sys.stdout.encoding}")
```

### 2. Inspect Bytes

```python
# See actual bytes
text = "✅"
print(f"UTF-8 bytes: {text.encode('utf-8')}")  # b'â'
print(f"CP437 decode: {text.encode('utf-8').decode('cp437', errors='replace')}")  # Γ£à
```

### 3. Use Encoding Fixtures

```python
from tests.encoding_fixtures import assert_no_mojibake, UNICODE_TEST_STRINGS

# Verify no mojibake
text = get_output_from_somewhere()
assert_no_mojibake(text, [UNICODE_TEST_STRINGS['emoji_checkmark']])
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Encoding Tests

on: [push, pull_request]

jobs:
  test-encoding:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest

    - name: Run encoding tests
      run: |
        pytest tests/test_subprocess_encoding.py -v
        pytest tests/test_file_io_unicode.py -v
        pytest tests/test_git_unicode.py -v
        pytest tests/test_console_encoding.py -v
```

## References

- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
- [PowerShell Character Encoding](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding)
- [Git Internationalization](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)
- [UTF-8 Everywhere Manifesto](http://utf8everywhere.org/)

## Summary

**Golden Rules:**
1. ✅ Always specify `encoding='utf-8'` for file operations
2. ✅ Use UTF-8 prefix for PowerShell subprocess calls
3. ✅ Test with actual unicode characters (emoji, Chinese, Arabic)
4. ✅ Use `assert_no_mojibake()` in tests
5. ✅ Document encoding assumptions in docstrings

**Never:**
1. ❌ Rely on system default encoding
2. ❌ Assume ASCII-only text
3. ❌ Skip encoding tests
4. ❌ Use `text=True` without `encoding='utf-8'` in subprocess
5. ❌ Ignore mojibake in test output
