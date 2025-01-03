import pytest
import os
import json
from bots.tools import github_tools
from datetime import datetime
READ_REPO = 'benbuzz790/bots'
WRITE_REPO = 'benbuzz790/test'


def generate_unique_name(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


@pytest.fixture
def created_issues():
    """Fixture to track and cleanup test issues"""
    issues = []
    yield issues
    for issue_number in issues:
        try:
            github_tools.update_issue(WRITE_REPO, issue_number, state='closed')
        except Exception as e:
            print(f'Failed to close issue {issue_number}: {e}')


def test_list_repositories():
    """Test listing repositories"""
    result = github_tools.list_repositories()
    assert not result.startswith('Error')
    repos = json.loads(result)
    assert isinstance(repos, list)
    assert len(repos) > 0
    assert any(repo == READ_REPO for repo in repos)


def test_list_issues():
    """Test listing issues"""
    result = github_tools.list_issues(READ_REPO)
    assert not result.startswith('Error')
    issues = json.loads(result)
    assert isinstance(issues, list)
    for issue in issues:
        assert 'number' in issue
        assert 'title' in issue
        assert 'state' in issue


def test_create_and_get_issue(created_issues):
    """Test creating a new issue"""
    issue_title = generate_unique_name('Test Issue')
    result = github_tools.create_issue(WRITE_REPO, issue_title,
        'This is a test issue')
    assert not result.startswith('Error')
    issue_info = json.loads(result)
    assert 'number' in issue_info
    assert 'url' in issue_info
    created_issues.append(issue_info['number'])
    list_result = github_tools.list_issues(WRITE_REPO)
    assert not list_result.startswith('Error')
    issues = json.loads(list_result)
    assert any(issue['number'] == issue_info['number'] for issue in issues)


def test_get_github_user_info():
    """Test getting authenticated user info"""
    result = github_tools.get_github_user_info()
    assert not result.startswith('Error')
    info = json.loads(result)
    assert isinstance(info, dict)
    assert 'login' in info
    assert 'name' in info
    assert 'public_repos' in info


def test_update_issue(created_issues):
    """Test updating an existing issue"""
    issue_title = generate_unique_name('Test Update Issue')
    result = github_tools.create_issue(WRITE_REPO, issue_title,
        'This is a test issue for updating')
    assert not result.startswith('Error')
    issue_info = json.loads(result)
    issue_number = issue_info['number']
    created_issues.append(issue_number)
    new_title = generate_unique_name('Updated Test Issue')
    update_result = github_tools.update_issue(WRITE_REPO, issue_number,
        title=new_title)
    assert not update_result.startswith('Error')
    updated_info = json.loads(update_result)
    assert updated_info['title'] == new_title
    update_result = github_tools.update_issue(WRITE_REPO, issue_number,
        state='closed')
    assert not update_result.startswith('Error')
    updated_info = json.loads(update_result)
    assert updated_info['state'] == 'closed'
    new_body = 'This is an updated test issue body'
    update_result = github_tools.update_issue(WRITE_REPO, issue_number,
        body=new_body)
    assert not update_result.startswith('Error')
    get_result = github_tools.get_issue(WRITE_REPO, issue_number)
    assert not get_result.startswith('Error')
    final_info = json.loads(get_result)
    assert final_info['title'] == new_title
    assert final_info['body'] == new_body
    assert final_info['state'] == 'closed'


def test_create_issue_unauthorized():
    """Test that create_issue fails when trying to create an issue in an unauthorized repo"""
    from bots.tools.github_tools import create_issue, list_repositories
    import json
    result = create_issue('facebook/react', 'Test Issue', 'Test Body')
    assert isinstance(result, str)
    assert 'Error: Not authorized' in result
    assert 'facebook/react' in result


def test_create_issue_authorized():
    """Test that create_issue succeeds when using an authorized repo"""
    from bots.tools.github_tools import create_issue, list_repositories
    import json
    repos = json.loads(list_repositories())
    if not repos:
        return
    test_repo = repos[0]
    result = create_issue(test_repo, 'Test Issue [AUTOMATED TEST]',
        'This is an automated test of the create_issue function. You can close this issue.'
        )
    result_dict = json.loads(result)
    assert 'number' in result_dict
    assert 'url' in result_dict
    assert isinstance(result_dict['number'], int)
    assert isinstance(result_dict['url'], str)


def test_normalize_repo_name():
    """Test repository name normalization with different input formats"""
    from bots.tools.github_tools import _normalize_repo_name
    assert _normalize_repo_name('owner/repo') == 'owner/repo'
    assert _normalize_repo_name({'repo': 'owner/repo'}) == 'owner/repo'
    assert _normalize_repo_name('{"repo": "owner/repo"}') == 'owner/repo'
    with pytest.raises(ValueError):
        _normalize_repo_name({})
    with pytest.raises(ValueError):
        _normalize_repo_name('')
    with pytest.raises(ValueError):
        _normalize_repo_name('invalid')
