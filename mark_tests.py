import os
import re


def add_markers_to_file(filepath, add_api=False, add_slow=False):
    """Add pytest markers to test functions in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False, "Could not read file"

    # Check if pytest is imported
    has_pytest_import = "import pytest" in content
    # Add pytest import if needed and markers are requested
    if (add_api or add_slow) and not has_pytest_import:
        # Find the last import statement
        import_pattern = r"^(import .*|from .* import .*)$"
        matches = list(re.finditer(import_pattern, content, re.MULTILINE))
        if matches:
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + "\nimport pytest" + content[insert_pos:]
        else:
            # No imports found, add at the beginning
            content = "import pytest\n\n" + content

    # Find all test functions and add markers
    modified = False

    # Pattern to match test function definitions
    test_func_pattern = r"^(\s*)def (test_\w+)\s*\("

    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(test_func_pattern, line)

        if match:
            indent = match.group(1)
            # Check if markers already exist in previous lines
            has_api_marker = False
            has_slow_marker = False

            # Look back at previous lines for existing markers
            j = i - 1
            while j >= 0 and (lines[j].strip().startswith("@") or lines[j].strip() == ""):
                if "@pytest.mark.api" in lines[j]:
                    has_api_marker = True
                if "@pytest.mark.slow" in lines[j]:
                    has_slow_marker = True
                j -= 1

            # Add markers if needed
            markers_to_add = []
            if add_api and not has_api_marker:
                markers_to_add.append(f"{indent}@pytest.mark.api")
            if add_slow and not has_slow_marker:
                markers_to_add.append(f"{indent}@pytest.mark.slow")

            if markers_to_add:
                new_lines.extend(markers_to_add)
                modified = True

        new_lines.append(line)
        i += 1

    if modified:
        content = "\n".join(new_lines)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True, "Markers added successfully"
        except Exception as e:
            return False, f"Could not write file: {e}"
    else:
        return False, "No modifications needed"


# Process files
results = {
    "integration": {"total": 0, "marked": 0, "skipped": 0},
    "e2e": {"total": 0, "marked": 0, "skipped": 0},
    "install": {"total": 0, "marked": 0, "skipped": 0},
}
# Mark integration tests (API only)
for root, dirs, files in os.walk("tests/integration"):
    for file in files:
        if file.startswith("test_") and file.endswith(".py"):
            filepath = os.path.join(root, file)
            results["integration"]["total"] += 1
            success, msg = add_markers_to_file(filepath, add_api=True, add_slow=False)
            if success:
                results["integration"]["marked"] += 1
            else:
                results["integration"]["skipped"] += 1
# Mark e2e tests (API + slow)
for root, dirs, files in os.walk("tests/e2e"):
    for file in files:
        if file.startswith("test_") and file.endswith(".py"):
            filepath = os.path.join(root, file)
            results["e2e"]["total"] += 1
            success, msg = add_markers_to_file(filepath, add_api=True, add_slow=True)
            if success:
                results["e2e"]["marked"] += 1
            else:
                results["e2e"]["skipped"] += 1
# Mark install tests (slow only)
for file in ["tests/test_install_in_fresh_environment.py", "tests/test_install_temp.py"]:
    if os.path.exists(file):
        results["install"]["total"] += 1
        success, msg = add_markers_to_file(file, add_api=False, add_slow=True)
        if success:
            results["install"]["marked"] += 1
        else:
            results["install"]["skipped"] += 1
print("MARKING COMPLETE (Second Pass):")
print(f'Integration tests: {results["integration"]["marked"]}/{results["integration"]["total"]} marked')
print(f'E2E tests: {results["e2e"]["marked"]}/{results["e2e"]["total"]} marked')
print(f'Install tests: {results["install"]["marked"]}/{results["install"]["total"]} marked')
print(f'Total: {sum(r["marked"] for r in results.values())}/{sum(r["total"] for r in results.values())} files marked')
