"""GitHub PR Comment Parser Utility.

This module provides tools to parse and extract comments from GitHub Pull Requests,
with special handling for CodeRabbit AI review comments.
"""

import json
import re
import subprocess
from typing import Dict, List, Optional


def get_pr_comments(pr_number: int, repo: str = "benbuzz790/bots") -> List[Dict]:
    """Fetch all comments from a GitHub PR using gh CLI.

    Parameters:
        pr_number (int): The PR number
        repo (str): Repository in format "owner/repo"

    Returns:
        List[Dict]: List of comment dictionaries
    """
    cmd = ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "comments"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return data.get("comments", [])


def extract_coderabbit_prompts(comment_body: str) -> Optional[str]:
    """Extract CodeRabbit AI prompt from a comment.

    Looks for the pattern:
    <summary>🤖 Prompt for AI Agents</summary>
    ```
    [prompt text]
    ```

    Parameters:
        comment_body (str): The comment body text

    Returns:
        Optional[str]: The extracted prompt text, or None if not found
    """
    # Pattern to match the CodeRabbit prompt section
    pattern = r"<summary>🤖 Prompt for AI Agents</summary>\s*```(.*?)```"
    match = re.search(pattern, comment_body, re.DOTALL)

    if match:
        return match.group(1).strip()
    return None


def is_outdated(comment: Dict) -> bool:
    """Check if a comment is marked as outdated.

    Parameters:
        comment (Dict): Comment dictionary from GitHub API

    Returns:
        bool: True if comment is outdated
    """
    # Check if the comment has an 'outdated' field
    if "outdated" in comment:
        return comment["outdated"]

    # Check if comment body contains outdated markers
    body = comment.get("body", "")
    outdated_markers = ["[outdated]", "~~outdated~~", "<!-- outdated -->"]
    return any(marker in body.lower() for marker in outdated_markers)


def parse_pr_comments(
    pr_number: int,
    repo: str = "benbuzz790/bots",
    output_file: Optional[str] = None,
    filter_coderabbit: bool = True,
    exclude_outdated: bool = True,
) -> List[Dict]:
    """Parse PR comments and optionally save to file.

    Parameters:
        pr_number (int): The PR number
        repo (str): Repository in format "owner/repo"
        output_file (Optional[str]): Path to save all comments (JSON format)
        filter_coderabbit (bool): If True, only return CodeRabbit prompts
        exclude_outdated (bool): If True, exclude outdated comments

    Returns:
        List[Dict]: Parsed comments with extracted information
    """
    comments = get_pr_comments(pr_number, repo)

    # Save all comments if requested
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(comments, f, indent=2)

    parsed_comments = []

    for comment in comments:
        # Skip outdated comments if requested
        if exclude_outdated and is_outdated(comment):
            continue

        body = comment.get("body", "")
        author = comment.get("author", {}).get("login", "unknown")

        # Check if this is a CodeRabbit comment
        is_coderabbit = author.lower() == "coderabbitai" or "coderabbit" in author.lower()

        if filter_coderabbit and not is_coderabbit:
            continue

        # Extract AI prompt if present
        ai_prompt = extract_coderabbit_prompts(body)

        if ai_prompt or not filter_coderabbit:
            parsed_comments.append(
                {
                    "author": author,
                    "body": body,
                    "ai_prompt": ai_prompt,
                    "created_at": comment.get("createdAt"),
                    "url": comment.get("url"),
                    "is_coderabbit": is_coderabbit,
                }
            )

    return parsed_comments


def save_coderabbit_prompts(pr_number: int, output_file: str, repo: str = "benbuzz790/bots") -> int:
    """Extract and save all CodeRabbit AI prompts from a PR.

    Parameters:
        pr_number (int): The PR number
        output_file (str): Path to save prompts (text format)
        repo (str): Repository in format "owner/repo"

    Returns:
        int: Number of prompts saved
    """
    parsed = parse_pr_comments(pr_number, repo=repo, filter_coderabbit=True, exclude_outdated=True)

    prompts = [c["ai_prompt"] for c in parsed if c["ai_prompt"]]

    with open(output_file, "w", encoding="utf-8") as f:
        for i, prompt in enumerate(prompts, 1):
            f.write(f"=== CodeRabbit Prompt #{i} ===\n")
            f.write(prompt)
            f.write("\n\n")

    return len(prompts)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pr_comment_parser.py <pr_number> [output_file]")
        sys.exit(1)

    pr_num = int(sys.argv[1])
    output = sys.argv[2] if len(sys.argv) > 2 else f"pr_{pr_num}_coderabbit_prompts.txt"

    count = save_coderabbit_prompts(pr_num, output)
    print(f"Extracted {count} CodeRabbit prompts to {output}")
