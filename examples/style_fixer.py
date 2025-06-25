"""Automated code style fixing system for CI/CD compliance for bots.
Use this module when you need to automatically fix code style issues across a
Python project to ensure CI/CD pipeline compliance using LLM-powered bots.
The module:
1. Finds all Python files in the project (excluding .gitignore patterns)
2. Pre-filters to only include files that fail style checks
3. Creates multiple bots to fix style issues in parallel
4. Uses par_branch_while to ensure thorough style fixing
5. Makes direct improvements using terminal tools and style formatters
This ensures all files pass Black, isort, flake8, and other style checks in
the CI/CD pipeline.
"""

import os
import subprocess
import textwrap
from typing import List, Tuple

from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode, Engines
from bots.tools import terminal_tools


def is_gitignored(file_path: str, project_root: str) -> bool:
    """Check if a file is ignored by git.
    Use when you need to determine if a file should be excluded from processing
    based on .gitignore rules.
    Parameters:
        file_path (str): Path to the file to check
        project_root (str): Root directory of the git repository
    Returns:
        bool: True if file is gitignored, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", file_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def find_python_files(start_path: str) -> List[str]:
    """Recursively find all Python files not in .gitignore.
    Use when you need to gather Python files for style fixing while respecting
    git ignore patterns and excluding files that shouldn't be processed.
    Parameters:
        start_path (str): Root directory to start search from. Should be the
                         project root.
    Returns:
        List[str]: List of absolute paths to Python files that should be
                  style-fixed
    """
    python_files = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if not is_gitignored(file_path, start_path):
                    python_files.append(file_path)
    return python_files


def passes_style_checks(file_path: str, project_root: str) -> bool:
    """Check if a Python file passes all style checks.
    Use when you need to determine if a file already complies with CI/CD
    style requirements and can be skipped from processing.
    Parameters:
        file_path (str): Absolute path to the Python file to check
        project_root (str): Root directory of the project
    Returns:
        bool: True if file passes all style checks, False if it needs fixing
    """
    rel_path = os.path.relpath(file_path, project_root)
    original_cwd = os.getcwd()

    try:
        # Change to project root for consistent tool execution
        os.chdir(project_root)

        # Check Black formatting
        try:
            black_result = subprocess.run(
                ["python", "-m", "black", "--check", rel_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if black_result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, Exception):
            return False

        # Check isort formatting
        try:
            isort_result = subprocess.run(
                ["python", "-m", "isort", "--check-only", rel_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if isort_result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, Exception):
            return False

        # Check flake8 linting
        try:
            flake8_result = subprocess.run(
                ["python", "-m", "flake8", rel_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if flake8_result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, Exception):
            return False

        return True

    finally:
        # Always restore original working directory
        os.chdir(original_cwd)


def find_files_needing_style_fixes(
    start_path: str,
) -> Tuple[List[str], List[str]]:
    """Find Python files that need style fixing, filtering out compliant ones.
    Use when you need to efficiently identify only the files that require
    style fixing, avoiding unnecessary processing of already-compliant files.
    Parameters:
        start_path (str): Root directory to start search from. Should be the
                         project root.
    Returns:
        Tuple[List[str], List[str]]:
            - List of absolute paths to Python files that need style fixing
            - List of absolute paths to Python files that already pass checks
    """
    all_python_files = find_python_files(start_path)
    files_needing_fixes = []
    files_already_passing = []

    print(f"Pre-filtering {len(all_python_files)} Python files...")

    for file_path in all_python_files:
        rel_path = os.path.relpath(file_path, start_path)
        print(f"Checking {rel_path}...", end=" ")

        if passes_style_checks(file_path, start_path):
            print("✓ PASSES")
            files_already_passing.append(file_path)
        else:
            print("✗ NEEDS FIXING")
            files_needing_fixes.append(file_path)

    return files_needing_fixes, files_already_passing


def check_file_cicd(file_path: str, project_root: str) -> str:
    """Run CI/CD style checks on a specific Python file.
    Parameters:
        file_path (str): Absolute path to the Python file to check
        project_root (str): Root directory of the project
    Returns:
        str: Detailed report of all style issues found, or confirmation if
             file passes all checks
    """
    rel_path = os.path.relpath(file_path, project_root)
    results = []
    original_cwd = os.getcwd()
    try:
        # Change to project root for consistent tool execution
        os.chdir(project_root)

        # Run Black check
        results.append("=== BLACK CHECK ===")
        try:
            black_result = subprocess.run(
                ["python", "-m", "black", "--check", "--diff", rel_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if black_result.returncode == 0:
                results.append("Black formatting: PASSED")
            else:
                results.append("Black formatting: FAILED")
                results.append("Black diff output:")
                results.append(black_result.stdout)
                if black_result.stderr:
                    results.append("Black errors:")
                    results.append(black_result.stderr)
        except subprocess.TimeoutExpired:
            results.append("Black check timed out")
        except Exception as e:
            results.append(f"Black check failed: {e}")

        # Run isort check
        results.append("\n=== ISORT CHECK ===")
        try:
            isort_result = subprocess.run(
                ["python", "-m", "isort", "--check-only", "--diff", rel_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if isort_result.returncode == 0:
                results.append("Import sorting: PASSED")
            else:
                results.append("Import sorting: FAILED")
                results.append("Isort diff output:")
                results.append(isort_result.stdout)
                if isort_result.stderr:
                    results.append("Isort errors:")
                    results.append(isort_result.stderr)
        except subprocess.TimeoutExpired:
            results.append("Isort check timed out")
        except Exception as e:
            results.append(f"Isort check failed: {e}")

        # Run flake8 check
        results.append("\n=== FLAKE8 CHECK ===")
        try:
            flake8_result = subprocess.run(
                [
                    "python",
                    "-m",
                    "flake8",
                    rel_path,
                    "--count",
                    "--statistics",
                    "--show-source",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
            if flake8_result.returncode == 0:
                results.append("Flake8 linting: PASSED")
            else:
                results.append("Flake8 linting: FAILED")
                results.append("Flake8 output:")
                results.append(flake8_result.stdout)
                if flake8_result.stderr:
                    results.append("Flake8 errors:")
                    results.append(flake8_result.stderr)
        except subprocess.TimeoutExpired:
            results.append("Flake8 check timed out")
        except Exception as e:
            results.append(f"Flake8 check failed: {e}")
    finally:
        # Always restore original working directory
        os.chdir(original_cwd)

    return "\n".join(results)


def create_style_fixer_bot(num: int, file_path: str, project_root: str) -> Bot:
    """Create and configure a bot specialized for fixing code style issues.
    Use when you need to create a new style-fixing bot instance with
    appropriate tools and context for fixing Python code style issues.
    Parameters:
        num (int): Unique identifier for the bot instance, used in naming
        file_path (str): Absolute path to the Python file this bot will work on
        project_root (str): Root directory of the project
    Returns:
        Bot: Configured AnthropicBot instance with:
            - Code style specialist role
            - Terminal tools for running commands
            - File-specific CI/CD checking tool
            - Appropriate system message for style fixing
    """
    rel_path = os.path.relpath(file_path, project_root)

    bot = AnthropicBot(
        model_engine=Engines.CLAUDE4_SONNET,  # Updated to Claude 4 Sonnet
        temperature=0.1,  # Low temperature for consistent style fixes
        name=f"StyleFixer{num}",
        role="Code Style Specialist",
        role_description=f"Fixes Python code style issues for {rel_path}",
        autosave=False,
    )

    # Add terminal tools for running commands and editing files
    import bots.tools.code_tools as ct
    import bots.tools.python_edit as pe
    import bots.tools.python_editing_tools as pet

    bot.add_tools(terminal_tools, pe, pet.replace_function, pet.replace_class, ct.view_dir, ct.view, ct.patch_edit)

    # Add file-specific CI/CD checking tool
    bot.add_tools(check_file_cicd)

    system_message = textwrap.dedent(
        f"""
        You are an expert in Python code style and CI/CD pipeline compliance.
        Your task is to fix code style issues in the file '{rel_path}' to
        ensure it passes automated style checks.

        Your assigned file: {rel_path}

        Your workflow:
        1. Use check_my_file() to identify current style issues
        2. Apply automatic formatters using execute_powershell:
           - python -m black {rel_path}
           - python -m isort {rel_path}
        3. For remaining issues, use patch_edit or view/edit files manually
        4. Use check_my_file() again to verify all issues are resolved

        Common manual fixes needed:
        - Line length violations: Break long lines at appropriate points
          but do not excessively shorten variable names. Descriptive var
          names are part of the author's style.
        - Bare except clauses: Change 'except:' to 'except Exception:'
        - Unused variables: Remove or prefix with underscore
        - F-strings without placeholders: Convert to regular strings (use double quotes)
        - Missing blank lines: Add proper spacing between functions/classes
        - 'raise NotImplemented': Change to 'raise NotImplementedError'

        IMPORTANT: Only work on your assigned file: {rel_path}
        Use the available tools to make direct edits. Do not change
        functionality, only style.

        IMPORTANT: You may decide that the file *should not* be formatted
        or otherwise adjusted. In that case, adjust the configuration file
        to ignore the file in question. As an example, test_python_edit.py
        contains many specific combinations of ", ', and escape characters
        and formatters are very likely to change functionality.

        IMPORTANT: If you see repeated code elements, and very large amounts
        of indentation you *may* refactor into smaller chunks, but only do
        this if it's completely necessary to meet line length limits.
        """
    ).strip()

    bot.set_system_message(system_message)
    return bot


def fix_file_style(bot: Bot) -> Tuple[List[str], List[ConversationNode]]:
    """Execute a thorough style fixing process for a Python file.
    Use when you need to systematically fix all style issues in a Python file
    to ensure CI/CD pipeline compliance.
    Parameters:
        bot (Bot): Configured style-fixing bot that has been initialized with
                  a target file path in its conversation context
    Returns:
        Tuple[List[str], List[ConversationNode]]:
            - List of responses from the style fixing process
            - List of conversation nodes tracking the fix history
    Note:
        The bot must be initialized with a TARGET FILE path before calling
        this function.
        The process includes:
        1. Initial style check analysis
        2. Automatic formatter application
        3. Manual fixes for remaining issues
        4. Final verification
    """
    prompts = [
        "INSTRUCTION: Start by running check_my_file() to see what style " "issues need to be fixed in your assigned file.",
        "INSTRUCTION: Now apply the automatic formatters to fix what can be "
        "automated. Use execute_powershell to run 'python -m black [your "
        "file path]' and 'python -m isort [your file path]'. Then run "
        "check_my_file() again to see what issues remain.",
        "INSTRUCTION: Fix any remaining flake8 issues manually. Focus on the "
        "most common issues like line length, bare except clauses, unused "
        "variables, and missing blank lines. Run check_my_file() after "
        "making changes to track progress.",
        "INSTRUCTION: Run check_my_file() one final time to verify all style "
        "issues are resolved. The file should now pass all CI/CD style "
        "checks.",
    ]

    def print_responses(responses, nodes):
        for response in responses:
            print("\n\n" + response)

    return fp.chain_while(
        bot=bot,
        prompt_list=prompts,
        stop_condition=fp.conditions.tool_not_used,
        continue_prompt="Once you have finished INSTRUCTION, write a brief "
        "summary of what you did and we will move to the next INSTRUCTION",
        callback=print_responses,
    )


def main():
    """Coordinate parallel style fixing across all Python files that need it.
    Use when you need to execute a full project style fix that:
    1. Identifies all relevant Python files (not in .gitignore)
    2. Pre-filters to only include files that fail style checks
    3. Creates parallel bot instances with file-specific tools
    4. Executes style fixing for each file that needs it
    5. Reports progress and summary
    """
    print("## Finding Files ##")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Find files that need fixing and those that already pass
    (
        files_needing_fixes,
        files_already_passing,
    ) = find_files_needing_style_fixes(project_root)

    print("\n## Summary ##")
    print(f"Files already passing style checks: {len(files_already_passing)}")
    print(f"Files needing style fixes: {len(files_needing_fixes)}")

    if files_already_passing:
        print("\nFiles already compliant:")
        for file in files_already_passing:
            rel_path = os.path.relpath(file, project_root)
            print(f"  ✓ {rel_path}")

    if not files_needing_fixes:
        print("\n?? All Python files already pass style checks! " "No fixes needed.")
        return

    print("\nFiles that need fixing:")
    for file in files_needing_fixes:
        rel_path = os.path.relpath(file, project_root)
        print(f"  ✗ {rel_path}")

    # Create bots only for files that need fixing
    print(f"\n## Creating {len(files_needing_fixes)} bots ##")
    bots = [create_style_fixer_bot(n, file, project_root) for n, file in enumerate(files_needing_fixes)]

    # Initialize each bot with its target file
    for bot, file in zip(bots, files_needing_fixes):
        rel_path = os.path.relpath(file, project_root)
        bot.respond(
            f"You are assigned to fix style issues in {rel_path}. This is "
            f"your TARGET FILE. Respond with 'ok' if you understand but do "
            f"not begin."
        )

    # Execute style fixing in parallel
    print(f"\n## Starting parallel style fixing for {len(bots)} files... ##")
    fp.par_dispatch(bots, fix_file_style)

    print(
        f"\n## Style fixing complete! ##"
        f"\nProcessed: {len(files_needing_fixes)} files"
        f"\nSkipped (already compliant): {len(files_already_passing)} files"
        f"\nAll files should now pass CI/CD style checks."
    )


if __name__ == "__main__":
    main()
