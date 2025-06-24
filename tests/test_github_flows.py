import gc
import pytest
import shutil
import subprocess
import time
from pathlib import Path
from bots.flows import functional_prompts as fp
from bots.flows.github_flows import clone_and_edit, clone_and_fp


@pytest.mark.skip("Not a reliable test. Needs update.")
def test_clone_and_edit():
    from tests.conftest import get_unique_filename
    # Use a temporary directory instead of hardcoded repo
    test_dir_name = get_unique_filename("test_clone_dir")
    test_dir = Path(test_dir_name)
    try:
        if test_dir.exists():
            gc.collect()
            time.sleep(1)
            shutil.rmtree(test_dir, ignore_errors=True)
    except Exception as e:
        print(f"Cleanup warning (non-fatal): {e}")
    # Create a temporary local git repository for testing instead of using external repo
    temp_repo_dir = Path(get_unique_filename("temp_test_repo"))
    try:
        # Create a minimal test repository
        temp_repo_dir.mkdir(exist_ok=True)
        (temp_repo_dir / "README.md").write_text("# Test Repository\nThis is a test file.")
        (temp_repo_dir / "test.py").write_text("print('Hello from test repo')")
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=temp_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_repo_dir, check=True, capture_output=True)
        repo_path = str(temp_repo_dir.absolute())
        task_prompt = "Please view the contents of this repository and \
            respond with just the word 'yes' if you can see any files."
        try:
            responses, nodes = clone_and_edit(test_dir, repo_path, task_prompt)
            clone_path = test_dir / temp_repo_dir.name
            print(f"\nDebug - Clone path exists: {clone_path.exists()}")
            if clone_path.exists():
                print("Files in clone_path:")
                for file in clone_path.rglob("*"):
                    print(f"  {file}")
            assert clone_path.exists(), "Repository was not cloned"
            bot_file = clone_path / f"{temp_repo_dir.name}_editor.bot"
            assert bot_file.exists(), "Bot file was not saved"
            print("\nBot responses:")
            for i, response in enumerate(responses):
                print(f"\nResponse {i}:\n{response}")
            assert len(responses) > 0, "No responses received"
            assert "yes" in responses[-1].lower(), "Bot did not confirm repository access"
        finally:
            for _ in range(3):
                try:
                    gc.collect()
                    time.sleep(1)
                    if test_dir.exists():
                        shutil.rmtree(test_dir, ignore_errors=True)
                    break
                except Exception as e:
                    print(f"Cleanup attempt failed: {e}")
                    continue
    finally:
        # Clean up temporary repo
        if temp_repo_dir.exists():
            try:
                shutil.rmtree(temp_repo_dir, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Could not clean temp repo {temp_repo_dir}: {e}")


def test_clone_and_fp_chain():
    from tests.conftest import get_unique_filename
    # Use a temporary directory instead of hardcoded repo
    test_dir_name = get_unique_filename("test_clone_dir")
    test_dir = Path(test_dir_name)
    try:
        if test_dir.exists():
            gc.collect()
            time.sleep(1)
            shutil.rmtree(test_dir, ignore_errors=True)
    except Exception as e:
        print(f"Cleanup warning (non-fatal): {e}")
    # Create a temporary local git repository for testing instead of using external repo
    temp_repo_dir = Path(get_unique_filename("temp_test_repo"))
    try:
        # Create a minimal test repository
        temp_repo_dir.mkdir(exist_ok=True)
        (temp_repo_dir / "README.md").write_text("# Test Repository\nThis is a test file.")
        (temp_repo_dir / "test.py").write_text("print('Hello from test repo')")
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=temp_repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_repo_dir, check=True, capture_output=True)
        repo_path = str(temp_repo_dir.absolute())
        clone_path = test_dir / temp_repo_dir.name
        prompts = [
            f"I've cloned the repository {repo_path} to {str(clone_path)}. "
            f"Use view_dir with target_extensions=['py', 'txt', 'md', 'git', 'idx', 'pack', 'rev'] "
            f"to see all files in {str(clone_path)}",
            "Respond with just the word 'yes' if you can see any files",
        ]
        try:
            responses, nodes = clone_and_fp(test_dir, repo_path, fp.chain, {"prompt_list": prompts})
            clone_path = test_dir / temp_repo_dir.name
            print(f"\nDebug - Clone path exists: {clone_path.exists()}")
            if clone_path.exists():
                print("Files in clone_path:")
                for file in clone_path.rglob("*"):
                    print(f"  {file}")
            assert clone_path.exists(), "Repository was not cloned"
            bot_file = clone_path / f"{temp_repo_dir.name}_editor.bot"
            assert bot_file.exists(), "Bot file was not saved"
            print("\nBot responses:")
            for i, response in enumerate(responses):
                print(f"\nResponse {i}:\n{response}")
            assert len(responses) > 0, "No responses received"
            assert "yes" in responses[-1].lower(), "Bot did not confirm repository access"
        finally:
            for _ in range(3):
                try:
                    gc.collect()
                    time.sleep(1)
                    if test_dir.exists():
                        shutil.rmtree(test_dir, ignore_errors=True)
                    break
                except Exception as e:
                    print(f"Cleanup attempt failed: {e}")
                    continue
    finally:
        # Clean up temporary repo
        if temp_repo_dir.exists():
            try:
                shutil.rmtree(temp_repo_dir, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Could not clean temp repo {temp_repo_dir}: {e}")
