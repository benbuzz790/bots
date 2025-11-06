# Test for Issue 162: Detect and prevent mojibake in source files
import re


def get_mojibake_patterns():
    return [
        (r"â†", "→", "right arrow"),
        (r"ΓåÆ", "→", "right arrow variant"),
        (r"âœ…", "✅", "checkmark"),
    ]


def check_file_for_mojibake(filepath):
    patterns = get_mojibake_patterns()
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        found = []
        for pattern, correct, description in patterns:
            matches = list(re.finditer(pattern, content))
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                lines = content.split("\n")
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                found.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "correct": correct,
                        "description": description,
                        "context": line_content.strip()[:100],
                    }
                )
        return found
    except Exception:
        return None


def test_cli_arrow_fixed():
    filepath = "bots/dev/cli.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if "marker = " in content:
        matches = list(re.finditer(r'marker = "([^"]*)"', content))
        for match in matches:
            marker_value = match.group(1)
            if "â†" in marker_value:
                line_num = content[: match.start()].count("\n") + 1
                raise AssertionError(f"Line {line_num} still has mojibake in marker: {marker_value}")
        print("✅ cli.py marker assignments are correct")


if __name__ == "__main__":
    print("Testing for mojibake...")
    test_cli_arrow_fixed()
    print("PASSED")
