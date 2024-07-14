import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from src import bots
import subprocess
from src import bot_tools

import time
class TestClaudeCapabilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claude = bots.AnthropicBot.load("data\Codey@2024.07.14-16.25.27.bot")
        cls.test_dir = os.path.join(os.getcwd(), 'claude_test_environment')
        os.makedirs(cls.test_dir, exist_ok=True)
    
    def execute_powershell(self, command):
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
        return result.stdout.strip()
    
    def test_self_translating_program(self):
        prompt = """
        Create a program that alternately translates itself between Python and C++ upon each run. The program should:
        1. Detect which language it's currently written in (Python or C++).
        2. Perform a simple task (e.g., print a fibonacci sequence up to the 10th number).
        3. Translate itself to the other language (Python to C++ or C++ to Python).
        4. Save the translated version, replacing the current file.
        5. Provide clear instructions on how to compile and run the C++ version.
        Use bot_tools to handle file operations. The initial implementation should be in Python.
        Ensure that both versions can be run multiple times, alternating between Python and C++.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "from bot_tools import *",
            "def detect_language(",
            "def fibonacci(",
            "def translate_to_cpp(",
            "def translate_to_python(",
            "bot_tools.rewrite(",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing implementation: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        self_translating_code = code_blocks[0]
        test_file_path = os.path.join(self.test_dir, 'self_translating_program.py')
        bot_tools.rewrite(test_file_path, self_translating_code)
        try:
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, "Python version failed to execute")
            self.assertIn("Fibonacci sequence", result.stdout, "Python version didn't print Fibonacci sequence")
        except subprocess.TimeoutExpired:
            self.fail("Python version execution timed out")
        cpp_file_path = os.path.join(self.test_dir, 'self_translating_program.cpp')
        self.assertTrue(os.path.exists(cpp_file_path), "C++ version was not created")
    
    def test_wing_design_optimization(self):
        prompt = """
        Create a Python program that optimizes wing design for an aircraft given the following requirements:
        1. Aircraft weight: 5000 kg
        2. Cruising speed: 250 m/s
        3. Cruising altitude: 10,000 m
        4. Desired range: 2000 km
        The program should:
        1. Use a simple aerodynamic model to calculate lift and drag.
        2. Optimize for the best lift-to-drag ratio.
        3. Consider variables such as wingspan, wing area, and aspect ratio.
        4. Use an optimization algorithm (e.g., gradient descent or genetic algorithm).
        5. Output the optimal wing design parameters and performance estimates.
        Use bot_tools to save the results to a file named 'wing_design_results.txt'.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "import numpy as np",
            "def calculate_lift(",
            "def calculate_drag(",
            "def objective_function(",
            "def optimize_wing_design(",
            "bot_tools.rewrite('wing_design_results.txt',",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing implementation: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        wing_design_code = code_blocks[0]
        test_file_path = os.path.join(self.test_dir, 'wing_design_optimization.py')
        bot_tools.rewrite(test_file_path, wing_design_code)
        try:
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, "Wing design optimization failed to execute")
            self.assertIn("Optimal wing design", result.stdout, "Program didn't output optimal wing design")
        except subprocess.TimeoutExpired:
            self.fail("Wing design optimization execution timed out")
        results_file = os.path.join(self.test_dir, 'wing_design_results.txt')
        self.assertTrue(os.path.exists(results_file), "Results file was not created")
        with open(results_file, 'r') as f:
            content = f.read()
            self.assertIn("Wingspan:", content)
            self.assertIn("Wing area:", content)
            self.assertIn("Aspect ratio:", content)
    
    def test_code_refactoring(self):
        poorly_written_code = """
    def do_stuff(x, y, z):
        a = x + y
        b = x - y
        c = z * (a + b)
        d = z / (a - b)
        e = a ** 2 + b ** 2 + c ** 2 + d ** 2
        f = math.sqrt(e)
        print(f"The result is: {f}")
        return f
    # Usage
    result = do_stuff(10, 5, 3)
    print(f"Final result: {result}")
        """
        test_file_path = os.path.join(self.test_dir, 'poorly_written_code.py')
        bot_tools.rewrite(test_file_path, poorly_written_code)
        prompt = f"""
        Refactor the Python function in the file '{test_file_path}' to improve its readability, efficiency, and adherence to best practices. The refactored code should:
        1. Use meaningful variable names
        2. Add type hints
        3. Include docstrings
        4. Handle potential errors (e.g., division by zero)
        5. Use f-strings for string formatting
        6. Follow PEP 8 style guidelines
        Use bot_tools to read the existing code and write the refactored version back to the same file.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "bot_tools.rewrite(",
            "def calculate_result(",
            "-> float:",
            "try:",
            "except ZeroDivisionError:",
            "return",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing implementation: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        refactored_code = code_blocks[0]
        with open(test_file_path, 'r') as f:
            content = f.read()
            self.assertEqual(content.strip(), refactored_code.strip(), "Refactored code was not written to the file")
        try:
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, "Refactored code failed to execute")
            self.assertIn("Final result:", result.stdout, "Refactored code didn't produce expected output")
        except subprocess.TimeoutExpired:
            self.fail("Refactored code execution timed out")
    
    def test_powershell_system_analysis(self):
        prompt = """
        Create a PowerShell script that performs the following system analysis tasks:
        1. List all running processes, sorted by CPU usage (top 10)
        2. Display disk usage for all drives
        3. Show network adapter information
        4. List installed Windows updates from the last 30 days
        The script should output the results to a file named 'system_analysis_results.txt'.
        Use bot_tools to write the PowerShell script to a file named 'system_analysis.ps1'.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "Get-Process",
            "Get-PSDrive",
            "Get-NetAdapter",
            "Get-HotFix",
            "Out-File",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing PowerShell cmdlet: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        powershell_script = code_blocks[0]
        script_path = os.path.join(self.test_dir, 'system_analysis.ps1')
        bot_tools.rewrite(script_path, powershell_script)
        try:
            result = self.execute_powershell(f"& '{script_path}'")
            self.assertNotIn("error", result.lower(), "PowerShell script execution resulted in an error")
            results_file = os.path.join(self.test_dir, 'system_analysis_results.txt')
            self.assertTrue(os.path.exists(results_file), "Results file was not created")
            with open(results_file, 'r') as f:
                content = f.read()
                self.assertIn("CPU Usage", content)
                self.assertIn("Disk Usage", content)
                self.assertIn("Network Adapter Information", content)
                self.assertIn("Recent Windows Updates", content)
        except Exception as e:
            self.fail(f"PowerShell script execution failed: {str(e)}")
    def test_design_pattern_implementation(self):
        prompt = """
        Implement the Observer design pattern in Python to create a simple file monitoring system. The system should:
        1. Have a FileSubject class that monitors a specific file for changes
        2. Have multiple FileObserver classes that react to file changes
        3. Use bot_tools to perform file operations
        Create a demo that:
        1. Sets up a FileSubject to monitor a file named 'observed_file.txt'
        2. Creates three FileObservers with different behaviors:
            a. One that logs changes to a 'file_changes.log' file
            b. One that creates a backup of the file when it changes
            c. One that sends a mock notification (print to console) when the file changes
        3. Demonstrates file changes and observer reactions
        Use bot_tools for all file operations in the implementation.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "class FileSubject:",
            "class FileObserver(",
            "class LoggingObserver(",
            "class BackupObserver(",
            "class NotificationObserver(",
            "bot_tools.rewrite(",
            "bot_tools.append(",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing implementation: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        observer_code = code_blocks[0]
        test_file_path = os.path.join(self.test_dir, 'file_observer_demo.py')
        bot_tools.rewrite(test_file_path, observer_code)
        try:
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, "Observer pattern demo failed to execute")
            self.assertIn("File changed", result.stdout, "Demo didn't show file change detection")
            self.assertIn("Notification", result.stdout, "Demo didn't show mock notification")
            log_file = os.path.join(self.test_dir, 'file_changes.log')
            self.assertTrue(os.path.exists(log_file), "Log file was not created")
            backup_file = os.path.join(self.test_dir, 'observed_file.txt.bak')
            self.assertTrue(os.path.exists(backup_file), "Backup file was not created")
        except subprocess.TimeoutExpired:
            self.fail("Observer pattern demo execution timed out")
    def test_performance_optimization(self):
        slow_code = """
    import time
    def slow_function(n):
        result = []
        for i in range(n):
            result.append(i)
            time.sleep(0.01)
        return result
    def process_data(data):
        result = []
        for item in data:
            result.append(item ** 2)
        return result
    def main():
        data = slow_function(100)
        processed_data = process_data(data)
        print(f"Processed {len(processed_data)} items")
    if __name__ == "__main__":
        main()
        """
        test_file_path = os.path.join(self.test_dir, 'slow_code.py')
        bot_tools.rewrite(test_file_path, slow_code)
        prompt = f"""
        Analyze the Python script in '{test_file_path}' for performance issues and optimize it. Your task is to:
        1. Use the cProfile module to profile the script and identify bottlenecks
        2. Suggest and implement optimizations to improve the script's performance
        3. Use bot_tools to modify the script with your optimizations
        4. Provide a brief explanation of the changes made and their impact
        Ensure that the optimized script produces the same output as the original.
        """
        response = self.claude.respond(prompt)
        required_elements = [
            "import cProfile",
            "bot_tools.rewrite(",
            "def optimized_slow_function(",
            "list comprehension",
            "generator",
        ]
        for element in required_elements:
            self.assertIn(element, response, f"Missing optimization: {element}")
        code_blocks, _ = bots.remove_code_blocks(response)
        if not code_blocks:
            self.fail("No code block found in the response")
        optimized_code = code_blocks[0]
        bot_tools.rewrite(test_file_path, optimized_code)
        try:
            start_time = time.time()
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, timeout=30)
            end_time = time.time()
            self.assertEqual(result.returncode, 0, "Optimized code failed to execute")
            self.assertIn("Processed 100 items", result.stdout, "Optimized code didn't produce expected output")
            execution_time = end_time - start_time
            self.assertLess(execution_time, 0.5, f"Optimized code took too long to execute: {execution_time:.2f} seconds")
        except subprocess.TimeoutExpired:
            self.fail("Optimized code execution timed out")
if __name__ == '__main__':
    unittest.main()