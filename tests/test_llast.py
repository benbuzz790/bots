import unittest
import tempfile
import os
import shutil
from pathlib import Path
import ast
from bots.tools.llast import LLASTProject, FileNode, DirectoryNode, FunctionNode, ClassNode

class TestLLAST(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a simple project structure
        self.main_py = os.path.join(self.test_dir, "main.py")
        self.utils_py = os.path.join(self.test_dir, "utils.py")
        
        # Create main.py with various Python constructs
        with open(self.main_py, "w") as f:
            f.write("""
def main():
    \"\"\"
    This is a multi-line docstring.
    It should be preserved exactly as it is.
    \"\"\"
    print("Hello, World!")
    
    if __name__ == "__main__":
        main()
        
class TestClass:
    \"\"\"Class docstring.\"\"\"
    def method(self):
        return "test"
        
async def async_func():
    return await something()
    
[x for x in range(10)]  # comprehension

match value:
    case 1:
        print("one")
    case _:
        print("other")

try:
    print('hello')
except Exception:
    print('I am sad')

""")

        # Create utils.py with different constructs
        with open(self.utils_py, "w") as f:
            f.write("""
def helper():
    \"\"\"Single line docstring\"\"\"
    try:
        return "helping"
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("done")
""")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_project_initialization(self):
        """Test basic project initialization and structure."""
        project = LLASTProject(self.test_dir)
        
        # Check root node
        self.assertIsNotNone(project.root)
        self.assertEqual(project.root.label, "0")
        self.assertIsInstance(project.root, DirectoryNode)
        
        # Check file nodes
        self.assertEqual(len(project.root.children), 2)
        self.assertIsInstance(project.root.children[0], FileNode)
        self.assertIsInstance(project.root.children[1], FileNode)

    def test_node_retrieval(self):
        """Test getting nodes by label."""
        project = LLASTProject(self.test_dir)
        
        # Test valid retrievals
        node = project.get_node("0.0")  # main.py
        self.assertIsNotNone(node)
        self.assertIsInstance(node, FileNode)
        
        # Test invalid retrieval
        node = project.get_node("invalid.label")
        self.assertIsNone(node)

    def test_string_preservation(self):
        """Test that string formatting is preserved."""
        project = LLASTProject(self.test_dir)
        main_file = project.get_node("0.0")
        
        # Check multi-line docstring
        func_node = project.get_node("0.0.0")  # main function
        self.assertIn("This is a multi-line docstring", func_node.to_source())
        
        # Check single-line docstring
        utils_file = project.get_node("0.1")
        helper_func = project.get_node("0.1.0")  # helper function
        self.assertIn("Single line docstring", helper_func.to_source())
    
    def test_node_modification(self):
        """Test modifying nodes."""
        project = LLASTProject(self.test_dir)
        
        # Get initial state
        main_func = project.get_node("0.0.0")
        print("\nINITIAL STATE:")
        print("-------------")
        print("Initial AST structure:")
        print("Main function children:", [type(c).__name__ for c in main_func.children])
        print("\nInitial source:")
        print(main_func.to_source())
        
        # Create new code - Note: no leading whitespace!
        new_code = """def main():
        \"\"\"Updated docstring\"\"\"
        print("Updated!")
    """
        print("\nUPDATE ATTEMPT:")
        print("--------------")
        print("New code to parse:")
        print(new_code)
        
        # Parse new code manually to verify AST structure
        try:
            parsed = ast.parse(new_code)
            print("\nParsed AST structure:")
            print(f"Number of body nodes: {len(parsed.body)}")
            print("Body node types:", [type(n).__name__ for n in parsed.body])
            if parsed.body:
                func_def = parsed.body[0]
                if isinstance(func_def, ast.FunctionDef):
                    print("Function body node types:", [type(n).__name__ for n in func_def.body])
                    for i, node in enumerate(func_def.body):
                        print(f"Body node {i}:", type(node).__name__)
                        if isinstance(node, ast.Expr):
                            print(f"  Expression value type:", type(node.value).__name__)
                            if isinstance(node.value, ast.Constant):
                                print(f"  Constant value:", repr(node.value.value))
        except Exception as e:
            print("Error parsing new code:", str(e))
        
        # Perform update
        result = project.update_node("0.0.0", new_code)
        print("Update result:", result)
        
        # Get updated state
        main_func = project.get_node("0.0.0")
        print("\nFINAL STATE:")
        print("-----------")
        print("Updated AST structure:")
        print("Main function children:", [type(c).__name__ for c in main_func.children])
        print("\nFinal source:")
        print(main_func.to_source())
        
        # Perform assertions with detailed output
        source = main_func.to_source()
        print("\nASSERTIONS:")
        print("-----------")
        print(f"Looking for 'Updated docstring' in: {repr(source)}")
        self.assertIn("Updated docstring", source, "Docstring was not updated correctly")
        
        print(f"Looking for print statement in: {repr(source)}")
        source_no_quotes = source.replace("'", "").replace('"', "")
        self.assertIn("print(Updated!)", source_no_quotes, "Print statement was not updated correctly")
        
        # Test overall structure
        self.assertIn("def main():", source, "Function definition is missing")
        self.assertTrue("print" in source and "Updated" in source, "Function body is missing expected content")

        # Print node hierarchy
        def print_hierarchy(node, level=0):
            print("  " * level + f"- {type(node).__name__}")
            for child in node.children:
                print_hierarchy(child, level + 1)
                
        print("\nNode hierarchy:")
        print_hierarchy(main_func)
        def test_node_insertion(self):
            """Test inserting new nodes."""
            project = LLASTProject(self.test_dir)
            
            # Insert a new function
            new_func = """
def new_function():
    return "new"
"""
            result = project.insert_child("0.1", new_func)
            self.assertIn("Inserted new node", result)
            
            # Verify the insertion
            utils_file = project.get_node("0.1")
            self.assertTrue(any("new_function" in child.to_source() 
                            for child in utils_file.children))

    def test_node_deletion(self):
        """Test deleting nodes."""
        project = LLASTProject(self.test_dir)
        
        # Delete a function
        result = project.delete("0.1.0")  # Delete helper function
        self.assertIn("Deleted node", result)
        
        # Verify the deletion
        utils_file = project.get_node("0.1")
        self.assertFalse(any("helper" in child.to_source() 
                            for child in utils_file.children))

    def test_special_syntax(self):
        """Test handling of special Python syntax."""
        project = LLASTProject(self.test_dir)
        
        # Test match statement
        match_node = None
        for node in project.root.children[0].children:  # main.py children
            if "match" in node.to_source():
                match_node = node
                break
        
        self.assertIsNotNone(match_node)
        self.assertIn("case 1:", match_node.to_source())
        self.assertIn("case _:", match_node.to_source())

    def test_control_flow(self):
        """Test handling of control flow statements."""
        project = LLASTProject(self.test_dir)
        
        # Find the try block in utils.py
        utils_file = project.get_node("0.1")
        try_block = None
        for node in utils_file.children[0].children:  # helper function children
            if "try:" in node.to_source():
                try_block = node
                break
                
        self.assertIsNotNone(try_block)
        source = try_block.to_source()
        self.assertIn("try:", source)
        self.assertIn("except Exception as e:", source)
        self.assertIn("finally:", source)

    def test_view_methods(self):
        """Test tree viewing methods."""
        project = LLASTProject(self.test_dir)
        
        # Test full tree view
        full_view = project.view_full_tree()
        self.assertIn("main.py", full_view)
        self.assertIn("utils.py", full_view)
        
        # Test expand view
        expanded = project.expand("0.0")  # Expand main.py
        self.assertIn("main.py", expanded)
        self.assertTrue(any("def main" in line for line in expanded.splitlines()))

    def test_error_handling(self):
        """Test error handling in various operations."""
        project = LLASTProject(self.test_dir)
        
        # Test invalid syntax
        bad_code = "def bad_function(:"  # Syntax error
        result = project.update_node("0.0.0", bad_code)
        self.assertIn("Syntax error", result)
        
        # Test invalid node label
        result = project.delete("nonexistent.node")
        self.assertIn("not found", result)
        
        # Test root node deletion
        result = project.delete("0")
        self.assertIn("Cannot delete the root node", result)

if __name__ == '__main__':
    unittest.main(verbosity=2)