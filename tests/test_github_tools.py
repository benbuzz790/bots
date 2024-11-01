import pytest
import os
import json
from bots.tools import github_tools
from datetime import datetime

# Set up test repository names
READ_REPO = "benbuzz790/bots"
WRITE_REPO = "benbuzz790/test"

def generate_unique_name(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

@pytest.fixture(scope="module")
def setup_test_repo():
    branch_name = generate_unique_name("test-branch")
    
    # Create a new branch
    branch_result = github_tools.create_branch(WRITE_REPO, branch_name)
    assert not branch_result.startswith("Error")

    # Create a file in the new branch
    file_result = github_tools.create_or_update_file(
        WRITE_REPO,
        "test-file.txt",
        "This is a test file for pull request",
        "Create test file for PR",
        branch=branch_name
    )
    assert not file_result.startswith("Error")

    yield branch_name

    # Cleanup: delete the test branch
    # Note: This assumes you have implemented a delete_branch function
    # If not, you may need to clean up manually or implement this function
    # delete_result = github_tools.delete_branch(WRITE_REPO, branch_name)
    # assert not delete_result.startswith("Error")

def test_list_repositories():
    result = github_tools.list_repositories()
    assert not result.startswith("Error")
    repos = json.loads(result)
    assert isinstance(repos, list)
    assert len(repos) > 0

def test_get_repository_info():
    result = github_tools.get_repository_info(READ_REPO)
    assert not result.startswith("Error")
    info = json.loads(result)
    assert isinstance(info, dict)
    assert "name" in info
    assert "description" in info

def test_list_branches():
    result = github_tools.list_branches(READ_REPO)
    assert not result.startswith("Error")
    branches = json.loads(result)
    assert isinstance(branches, list)
    assert len(branches) > 0

def test_get_file_content():
    result = github_tools.get_file_content(READ_REPO, "README.md")
    assert not result.startswith("Error")
    assert len(result) > 0

def test_list_issues():
    result = github_tools.list_issues(READ_REPO)
    assert not result.startswith("Error")
    issues = json.loads(result)
    assert isinstance(issues, list)

def test_list_pull_requests():
    result = github_tools.list_pull_requests(READ_REPO)
    assert not result.startswith("Error")
    prs = json.loads(result)
    assert isinstance(prs, list)

def test_search_repositories():
    result = github_tools.search_repositories("python")
    assert not result.startswith("Error")
    repos = json.loads(result)
    assert isinstance(repos, list)
    assert len(repos) > 0

def test_get_user_info():
    result = github_tools.get_user_info()
    assert not result.startswith("Error")
    info = json.loads(result)
    assert isinstance(info, dict)
    assert "login" in info
    assert "name" in info

def test_list_repository_contents():
    result = github_tools.list_repository_contents(READ_REPO)
    assert not result.startswith("Error")
    contents = json.loads(result)
    assert isinstance(contents, list)
    assert len(contents) > 0

def test_create_issue():
    issue_title = generate_unique_name("Test Issue")
    result = github_tools.create_issue(WRITE_REPO, issue_title, "This is a test issue")
    assert not result.startswith("Error")
    issue = json.loads(result)
    assert "number" in issue
    assert "url" in issue

def test_create_or_update_file():
    file_name = generate_unique_name("test_file") + ".txt"
    result = github_tools.create_or_update_file(WRITE_REPO, file_name, "Test content", "Test commit")
    assert not result.startswith("Error")
    file_info = json.loads(result)
    assert "commit_sha" in file_info
    assert "file_path" in file_info

def test_delete_file():
    file_name = generate_unique_name("test_file") + ".txt"
    # First, create a file
    create_result = github_tools.create_or_update_file(WRITE_REPO, file_name, "Test content", "Create test file")
    assert not create_result.startswith("Error")
    
    # Then, delete the file
    result = github_tools.delete_file(WRITE_REPO, file_name, "Delete test file")
    assert not result.startswith("Error")
    delete_info = json.loads(result)
    assert "commit_sha" in delete_info

def test_create_branch():
    branch_name = generate_unique_name("test-branch")
    result = github_tools.create_branch(WRITE_REPO, branch_name)
    assert not result.startswith("Error")
    branch_info = json.loads(result)
    assert "ref" in branch_info
    assert "sha" in branch_info

def test_create_and_merge_pull_request(setup_test_repo):
    branch_name = setup_test_repo
    pr_title = generate_unique_name("Test PR")
    
    # Create pull request
    create_pr_result = github_tools.create_pull_request(
        WRITE_REPO,
        pr_title,
        branch_name,
        "main",
        "This is a test PR"
    )
    assert not create_pr_result.startswith("Error")
    pr_info = json.loads(create_pr_result)
    assert "number" in pr_info
    assert "url" in pr_info

    # Merge pull request
    merge_result = github_tools.merge_pull_request(WRITE_REPO, pr_info["number"], "Merging test PR")
    assert not merge_result.startswith("Error")
    merge_info = json.loads(merge_result)
    assert "merged" in merge_info
    assert merge_info["merged"] == True
    assert "sha" in merge_info

def test_update_repository_settings():
    new_description = f"Updated test description {datetime.now().strftime('%Y%m%d%H%M%S')}"
    result = github_tools.update_repository_settings(WRITE_REPO, description=new_description)
    assert not result.startswith("Error")
    repo_info = json.loads(result)
    assert "description" in repo_info
    assert repo_info["description"] == new_description
    assert repo_info["description"].startswith("Updated test description")
