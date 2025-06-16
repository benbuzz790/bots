import pytest
from pathlib import Path
import shutil
from bots.flows.github_flows import clone_and_edit, clone_and_fp
import time
import os
from bots.flows import functional_prompts as fp

def test_clone_and_edit():
    test_dir = Path('test_clone_dir')
    try:
        if test_dir.exists():
            import gc
            gc.collect()
            time.sleep(1)
            shutil.rmtree(test_dir, ignore_errors=True)
    except Exception as e:
        print(f'Cleanup warning (non-fatal): {e}')
    repo_name = 'benbuzz790/private_tests'
    task_prompt = "Please view the contents of this repository and respond with just the word 'yes' if you can see any files."
    try:
        responses, nodes = clone_and_edit(test_dir, repo_name, task_prompt)
        clone_path = test_dir / 'private_tests'
        print(f'\nDebug - Clone path exists: {clone_path.exists()}')
        if clone_path.exists():
            print('Files in clone_path:')
            for file in clone_path.rglob('*'):
                print(f'  {file}')
        assert clone_path.exists(), 'Repository was not cloned'
        bot_file = clone_path / f'{repo_name}_editor.bot'
        assert bot_file.exists(), 'Bot file was not saved'
        print('\nBot responses:')
        for i, response in enumerate(responses):
            print(f'\nResponse {i}:\n{response}')
        assert len(responses) > 0, 'No responses received'
        assert 'yes' in responses[-1].lower(), 'Bot did not confirm repository access'
    finally:
        for _ in range(3):
            try:
                gc.collect()
                time.sleep(1)
                if test_dir.exists():
                    shutil.rmtree(test_dir, ignore_errors=True)
                break
            except Exception as e:
                print(f'Cleanup attempt failed: {e}')
                continue

def test_clone_and_fp_chain():
    test_dir = Path('test_clone_dir')
    try:
        if test_dir.exists():
            import gc
            gc.collect()
            time.sleep(1)
            shutil.rmtree(test_dir, ignore_errors=True)
    except Exception as e:
        print(f'Cleanup warning (non-fatal): {e}')
    repo_name = 'benbuzz790/private_tests'
    clone_path = test_dir / 'private_tests'
    prompts = [f"I've cloned the repository {repo_name} to {str(clone_path)}. Use view_dir with target_extensions=['py', 'txt', 'md', 'git', 'idx', 'pack', 'rev'] to see all files in {str(clone_path)}", "Respond with just the word 'yes' if you can see any files"]
    try:
        responses, nodes = clone_and_fp(test_dir, repo_name, fp.chain, {'prompt_list': prompts})
        clone_path = test_dir / 'private_tests'
        print(f'\nDebug - Clone path exists: {clone_path.exists()}')
        if clone_path.exists():
            print('Files in clone_path:')
            for file in clone_path.rglob('*'):
                print(f'  {file}')
        assert clone_path.exists(), 'Repository was not cloned'
        bot_file = clone_path / f'{repo_name}_editor.bot'
        assert bot_file.exists(), 'Bot file was not saved'
        print('\nBot responses:')
        for i, response in enumerate(responses):
            print(f'\nResponse {i}:\n{response}')
        assert len(responses) > 0, 'No responses received'
        assert 'yes' in responses[-1].lower(), 'Bot did not confirm repository access'
    finally:
        for _ in range(3):
            try:
                gc.collect()
                time.sleep(1)
                if test_dir.exists():
                    shutil.rmtree(test_dir, ignore_errors=True)
                break
            except Exception as e:
                print(f'Cleanup attempt failed: {e}')
                continue
