import subprocess
import json
def get_feedback(pr_id: str, repo: str = "promptfoo/promptfoo") -> str:
    """Extract feedback from GitHub PR reviews."""
    try:
        cmd = ["gh", "api", f"repos/{repo}/pulls/{pr_id}/reviews"]
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              timeout=30, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"
if __name__ == "__main__":
    print("test")
