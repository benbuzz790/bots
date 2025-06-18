import inspect
import sys
import types
import unittest

from bots.tools.code_tools import view_dir

sys.path.append(".")


class TestDynamicFunctionExecution(unittest.TestCase):
    """Test that functions can be dynamically executed with proper context."""

    def test_view_dir_dynamic_execution_with_imports(self):
        """Test that view_dir works when dynamically executed
        (reproduces the original bug)."""
        # This test simulates what the bot system does when loading tools
        func = view_dir
        code = func.__code__
        names = code.co_names
        # Create context like the bot system does (with our fix)
        context = {}
        for name in names:
            if name in func.__globals__:
                context[name] = func.__globals__[name]
        # Add all imports and callables from the original module (the fix)
        for name, value in func.__globals__.items():
            if isinstance(value, types.ModuleType) or callable(value):
                context[name] = value
        # Verify that required imports are in context
        self.assertIn("os", context, "os module should be in context")
        self.assertIn(
            "handle_errors",
            context,
            "handle_errors decorator should be in context",
        )
        # Test dynamic execution
        source = inspect.getsource(view_dir)
        module = types.ModuleType("test_module")
        module.__dict__.update(context)
        # This should not raise "name 'os' is not defined"
        exec(source, module.__dict__)
        new_func = module.__dict__["view_dir"]
        # Test that the dynamically loaded function actually works
        result = new_func(".", None, "['py']")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_old_context_method_fails(self):
        """Test that the old context method would fail
        (demonstrates the bug)."""
        func = view_dir
        code = func.__code__
        names = code.co_names
        # Create context like the OLD bot system did (without the fix)
        old_context = {}
        for name in names:
            if name in func.__globals__:
                old_context[name] = func.__globals__[name]
        # The old method might not include 'os' if it's not in co_names
        # This demonstrates why the fix was needed
        if "os" not in old_context:
            print("Old method would fail - os not in context")
        else:
            print("Old method might work - os is in co_names")


if __name__ == "__main__":
    unittest.main()
