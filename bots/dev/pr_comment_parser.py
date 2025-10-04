"""GitHub PR Comment Parser Utility.

This module provides tools to parse and extract comments from GitHub Pull Requests,
with special handling for CodeRabbit AI review comments.
"""

import json
import re
from typing import List, Dict, Optional
import subprocess


def get_pr_comments(pr_number: int, repo: str) -> List[Dict]:
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


def get_pr_review_comments(pr_number: int, repo: str) -> List[Dict]:
    """Fetch all review comments (inline comments) from a GitHub PR using gh CLI.

    Parameters:
        pr_number (int): The PR number
        repo (str): Repository in format "owner/repo"

    Returns:
        List[Dict]: List of review comment dictionaries
    """
    # Get review comments (inline comments on code)
    cmd = ["gh", "api", f"/repos/{repo}/pulls/{pr_number}/comments"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


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
    repo: str,
    output_file: Optional[str] = None,
    filter_coderabbit: bool = True,
    exclude_outdated: bool = True,
    include_review_comments: bool = True,
) -> List[Dict]:
    """Parse PR comments and optionally save to file.

    Parameters:
        pr_number (int): The PR number
        repo (str): Repository in format "owner/repo"
        output_file (Optional[str]): Path to save all comments (JSON format)
        filter_coderabbit (bool): If True, only return CodeRabbit prompts
        exclude_outdated (bool): If True, exclude outdated comments
        include_review_comments (bool): If True, also fetch inline review comments

    Returns:
        List[Dict]: Parsed comments with extracted information
    """
    # Get regular comments
    comments = get_pr_comments(pr_number, repo)

    # Also get review comments (inline comments)
    if include_review_comments:
        review_comments = get_pr_review_comments(pr_number, repo)
        # Normalize review comment format to match regular comments
        for rc in review_comments:
            rc["author"] = {"login": rc.get("user", {}).get("login", "unknown")}
            rc["createdAt"] = rc.get("created_at")
        comments.extend(review_comments)

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
                    "created_at": comment.get("createdAt") or comment.get("created_at"),
                    "url": comment.get("url") or comment.get("html_url"),
                    "is_coderabbit": is_coderabbit,
                }
            )

    return parsed_comments


def save_coderabbit_prompts(pr_number: int, repo: str, output_file: Optional[str] = None) -> int:
    """Extract and save all CodeRabbit AI prompts from a PR.

    Parameters:
        pr_number (int): The PR number
        output_file (Optional[str]): Path to save prompts (text format). If None, prints to stdout.
        repo (str): Repository in format "owner/repo"

    Returns:
        int: Number of prompts saved
    """
    parsed = parse_pr_comments(
        pr_number, repo=repo, filter_coderabbit=True, exclude_outdated=True, include_review_comments=True
    )

    prompts = [c["ai_prompt"] for c in parsed if c["ai_prompt"]]

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            for i, prompt in enumerate(prompts, 1):
                f.write(f"=== CodeRabbit Prompt #{i} ===\n")
                f.write(prompt)
                f.write("\n\n")
    else:
        # Print to stdout
        for i, prompt in enumerate(prompts, 1):
            print(f"=== CodeRabbit Prompt #{i} ===")
            print(prompt)
            print()

    return len(prompts)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pr_comment_parser.py <repo> <pr_number> [output_file]")
        print("  repo: Repository in format 'owner/repo'")
        print("  pr_number: The PR number")
        print("  output_file: Optional file to save prompts (prints to stdout if omitted)")
        print("\nExample: python pr_comment_parser.py owner/repo 123")
        sys.exit(1)

    repo = sys.argv[1]
    pr_num = int(sys.argv[2])
    output = sys.argv[3] if len(sys.argv) > 3 else None

    count = save_coderabbit_prompts(pr_num, repo, output)

    if output:
        print(f"Extracted {count} CodeRabbit prompts to {output}")
    else:
        print(f"\n--- Extracted {count} CodeRabbit prompts ---", file=sys.stderr)
