
import os
import bot_tools

def test_delete_match():
    # Create a temporary test file
    test_file = 'test_delete_match.txt'
    with open(test_file, 'w') as f:
        f.write("Line 1: Keep this\nLine 2: Delete me\nLine 3: Keep this too\nLine 4: Also DELETE\n")
    
    # Run the delete_match function
    bot_tools.delete_match(test_file, "Delete")
    
    # Check the result
    with open(test_file, 'r') as f:
        content = f.read()
    
    expected = "Line 1: Keep this\nLine 3: Keep this too\n"
    assert content == expected, f"Expected:\n{expected}\nBut got:\n{content}"
    
    # Clean up
    os.remove(test_file)
    print("test_delete_match passed successfully")

if __name__ == '__main__':
    test_delete_match()
