#!/usr/bin/env python3
import sys
sys.path.append('bots')
from bots.tools.code_tools import patch_edit
# Test the failing case
orig_code = (
    "class MyClass:\n"
    "    def foo(self):\n"
    "        pass\n"
)
patch = """@@ -2,6 +2,10 @@
    def foo(self):
        pass
+
+    def bar(self):
+        print("bar!")
"""
print("Original code:")
print(repr(orig_code))
print("\nPatch:")
print(repr(patch))
# Write to temp file and apply patch
import tempfile
with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.py') as tf:
    tf.write(orig_code)
    tf.flush()
    result = patch_edit(tf.name, patch)
    print(f"\nPatch result: {result}")
    with open(tf.name, 'r') as f:
        actual_result = f.read()
    print("\nActual result:")
    print(repr(actual_result))
    expected = (
        "class MyClass:\n"
        "    def foo(self):\n"
        "        pass\n"
        "\n"
        "    def bar(self):\n"
        "        print(\"bar!\")\n"
    )
    print("\nExpected result:")
    print(repr(expected))
    print(f"\nMatch: {actual_result == expected}")
    if actual_result != expected:
        print("\nDifferences:")
        for i, (a, e) in enumerate(zip(actual_result.split('\n'), expected.split('\n'))):
            if a != e:
                print(f"Line {i}: got {repr(a)}, expected {repr(e)}")
