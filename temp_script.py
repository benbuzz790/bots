import subprocess

def run_git_command(command):
    try:
        result = subprocess.run(["git"] + command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

# Stage all changes
print(run_git_command(["add", "."]))

# Create a temporary commit
commit_message = "Temporary commit: Removed .gitignore and gitignore.py"
print(run_git_command(["commit", "-m", commit_message]))

# Show the latest commit
print("\nLatest commit:")
print(run_git_command(["log", "-1", "--oneline"]))

# Show status to confirm everything is committed
print("\nGit status:")
print(run_git_command(["status"]))