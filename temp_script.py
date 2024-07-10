import subprocess

def git_commit(message):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        return "Git commit successful."
    except subprocess.CalledProcessError as e:
        return f"Git commit failed: {e}"

commit_message = "Update test_error_handling in test_bot_tools.py"
result = git_commit(commit_message)
print(result)