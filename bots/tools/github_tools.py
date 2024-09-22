import json
from ghapi.all import GhApi
import base64
import os

def _setup():
    """
    Internal function to set up the GitHub API client.
    
    This function looks for a GitHub token in the environment variables.
    It checks for GITHUB_TOKEN first, then GITHUB_ACCESS_TOKEN.
    If neither is found, it raises an exception.
    
    Returns:
    GhApi: An instance of the GitHub API client.
    
    Raises:
    ValueError: If neither GITHUB_TOKEN nor GITHUB_ACCESS_TOKEN environment variable is set.
    """
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GITHUB_ACCESS_TOKEN')
    if not token:
        raise ValueError("Neither GITHUB_TOKEN nor GITHUB_ACCESS_TOKEN environment variable is set. "
                         "Please set one of them with your GitHub Personal Access Token.")
    return GhApi(token=token)

def list_repositories():
    """
    List all repositories for the authenticated user.

    Use when you need to get an overview of all repositories the user has access to.

    Parameters:
    None

    Returns a JSON string containing an array of repository full names (owner/repo).
    """
    try:
        api = _setup()
        repos = api.repos.list_for_authenticated_user()
        return json.dumps([repo.full_name for repo in repos])
    except Exception as e:
        return f"Error: {str(e)}"

def get_repository_info(repo_full_name):
    """
    Get basic information about a specific repository.

    Use when you need to retrieve key details about a repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".

    Returns a JSON string containing repository information (name, description, stars, forks).
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        repo_info = api.repos.get(owner=owner, repo=repo)
        return json.dumps({
            "name": repo_info.name,
            "description": repo_info.description,
            "stars": repo_info.stargazers_count,
            "forks": repo_info.forks_count
        })
    except Exception as e:
        return f"Error: {str(e)}"

def list_branches(repo_full_name):
    """
    List all branches in a repository.

    Use when you need to see all the branches available in a specific repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".

    Returns a JSON string containing an array of branch names.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        branches = api.repos.list_branches(owner=owner, repo=repo)
        return json.dumps([branch.name for branch in branches])
    except Exception as e:
        return f"Error: {str(e)}"

def get_file_content(repo_full_name, file_path, branch='main'):
    """
    Get the content of a file in a repository.

    Use when you need to retrieve the contents of a specific file from a repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - file_path (str): The path to the file within the repository.
    - branch (str): The branch to get the file from (default is 'main').

    Returns a string containing the content of the file.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        content = api.repos.get_content(owner=owner, repo=repo, path=file_path, ref=branch)
        return content.content
    except Exception as e:
        return f"Error: {str(e)}"

def create_issue(repo_full_name, title, body):
    """
    Create a new issue in a repository.

    Use when you need to open a new issue in a specific repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - title (str): The title of the issue.
    - body (str): The body content of the issue.

    Returns a JSON string containing the issue number and URL.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        issue = api.issues.create(owner=owner, repo=repo, title=title, body=body)
        return json.dumps({
            "number": issue.number,
            "url": issue.html_url
        })
    except Exception as e:
        return f"Error: {str(e)}"

def list_issues(repo_full_name, state='open'):
    """
    List issues in a repository.

    Use when you need to get an overview of issues in a specific repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - state (str): The state of issues to list ('open', 'closed', or 'all', default is 'open').

    Returns a JSON string containing an array of issues with their number, title, and state.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        issues = api.issues.list_for_repo(owner=owner, repo=repo, state=state)
        return json.dumps([{
            "number": issue.number,
            "title": issue.title,
            "state": issue.state
        } for issue in issues])
    except Exception as e:
        return f"Error: {str(e)}"

def create_pull_request(repo_full_name, title, head, base, body):
    """
    Create a new pull request in a repository.

    Use when you need to open a new pull request to merge changes from one branch to another.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - title (str): The title of the pull request.
    - head (str): The name of the branch where your changes are implemented.
    - base (str): The name of the branch you want the changes pulled into.
    - body (str): The body content of the pull request.

    Returns a JSON string containing the pull request number and URL.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        pr = api.pulls.create(owner=owner, repo=repo, title=title, head=head, base=base, body=body)
        return json.dumps({
            "number": pr.number,
            "url": pr.html_url
        })
    except Exception as e:
        return f"Error: {str(e)}"

def list_pull_requests(repo_full_name, state='open'):
    """
    List pull requests in a repository.

    Use when you need to get an overview of pull requests in a specific repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - state (str): The state of pull requests to list ('open', 'closed', or 'all', default is 'open').

    Returns a JSON string containing an array of pull requests with their number, title, and state.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        prs = api.pulls.list(owner=owner, repo=repo, state=state)
        return json.dumps([{
            "number": pr.number,
            "title": pr.title,
            "state": pr.state
        } for pr in prs])
    except Exception as e:
        return f"Error: {str(e)}"

def search_repositories(query):
    """
    Search for repositories based on a query.

    Use when you need to find repositories matching specific criteria.

    Parameters:
    - query (str): The search query string.

    Returns a JSON string containing an array of the top 10 repository results with their full name, description, and star count.
    """
    try:
        api = _setup()
        results = api.search.repos(q=query)
        return json.dumps([{
            "full_name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count
        } for repo in results.items[:10]])  # Limit to top 10 results
    except Exception as e:
        return f"Error: {str(e)}"

def get_user_info():
    """
    Get information about the authenticated user.

    Use when you need to retrieve details about the current user's GitHub account.

    Parameters:
    None

    Returns a JSON string containing user information (login, name, email, public repository count).
    """
    try:
        api = _setup()
        user = api.users.get_authenticated()
        return json.dumps({
            "login": user.login,
            "name": user.name,
            "email": user.email,
            "public_repos": user.public_repos
        })
    except Exception as e:
        return f"Error: {str(e)}"

def create_or_update_file(repo_full_name, file_path, content, commit_message, branch='main'):
    """
    Create a new file or update an existing file in a repository.

    Use when you need to add a new file or modify an existing one in a repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - file_path (str): The path where the file should be created or updated.
    - content (str): The content of the file.
    - commit_message (str): The commit message for this change.
    - branch (str): The branch to commit to (default is 'main').

    Returns a JSON string containing the commit SHA and file information.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        # Check if file already exists
        try:
            existing_file = api.repos.get_content(owner=owner, repo=repo, path=file_path, ref=branch)
            sha = existing_file.sha
        except:
            sha = None

        # Encode content to base64
        content_bytes = content.encode('utf-8')
        content_base64 = base64.b64encode(content_bytes).decode('utf-8')

        result = api.repos.create_or_update_file_contents(
            owner=owner,
            repo=repo,
            path=file_path,
            message=commit_message,
            content=content_base64,
            sha=sha,
            branch=branch
        )
        return json.dumps({
            "commit_sha": result.commit.sha,
            "file_path": file_path
        })
    except Exception as e:
        return f"Error: {str(e)}"

def delete_file(repo_full_name, file_path, commit_message, branch='main'):
    """
    Delete a file from a repository.

    Use when you need to remove a file from a repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - file_path (str): The path of the file to be deleted.
    - commit_message (str): The commit message for this deletion.
    - branch (str): The branch to commit to (default is 'main').

    Returns a JSON string containing the commit SHA.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        # Get the file's SHA
        file_info = api.repos.get_content(owner=owner, repo=repo, path=file_path, ref=branch)
        
        result = api.repos.delete_file(
            owner=owner,
            repo=repo,
            path=file_path,
            message=commit_message,
            sha=file_info.sha,
            branch=branch
        )
        return json.dumps({
            "commit_sha": result.commit.sha
        })
    except Exception as e:
        return f"Error: {str(e)}"

def create_branch(repo_full_name, new_branch_name, base_branch='main'):
    """
    Create a new branch in a repository.

    Use when you need to create a new branch for making changes without affecting the main codebase.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - new_branch_name (str): The name of the new branch to create.
    - base_branch (str): The name of the branch to base the new branch on (default is 'main').

    Returns a JSON string containing the new branch's ref and SHA.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        # Get the SHA of the base branch
        base_branch_ref = api.git.get_ref(owner=owner, repo=repo, ref=f"heads/{base_branch}")
        base_sha = base_branch_ref.object.sha
        
        # Create the new branch
        new_branch = api.git.create_ref(
            owner=owner,
            repo=repo,
            ref=f"refs/heads/{new_branch_name}",
            sha=base_sha
        )
        return json.dumps({
            "ref": new_branch.ref,
            "sha": new_branch.object.sha
        })
    except Exception as e:
        return f"Error: {str(e)}"

def merge_pull_request(repo_full_name, pull_number, commit_message=None):
    """
    Merge a pull request.

    Use when you need to incorporate approved changes from a pull request into the base branch.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - pull_number (int): The number of the pull request to merge.
    - commit_message (str, optional): The message to use for the merge commit. If None, GitHub will auto-generate one.

    Returns a JSON string containing the SHA of the merge commit.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        result = api.pulls.merge(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            commit_message=commit_message
        )
        return json.dumps({
            "merged": result.merged,
            "message": result.message,
            "sha": result.sha
        })
    except Exception as e:
        return f"Error: {str(e)}"

def list_repository_contents(repo_full_name, path='', ref='main'):
    """
    List contents of a repository directory.

    Use when you need to view the current structure and files in a repository.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - path (str): The directory path to list contents for. Empty string for root directory.
    - ref (str): The name of the commit/branch/tag. Default: the repository's default branch (usually 'main').

    Returns a JSON string containing an array of file and directory information.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        contents = api.repos.get_content(owner=owner, repo=repo, path=path, ref=ref)
        return json.dumps([{
            "name": item.name,
            "path": item.path,
            "type": item.type,
            "size": item.size,
            "sha": item.sha
        } for item in contents])
    except Exception as e:
        return f"Error: {str(e)}"

def update_repository_settings(repo_full_name, **kwargs):
    """
    Update repository settings.

    Use when you need to modify repository configurations.

    Parameters:
    - repo_full_name (str): The full name of the repository in the format "owner/repo".
    - **kwargs: Arbitrary keyword arguments representing the settings to update.
      Possible keys include: 'name', 'description', 'homepage', 'private', 'has_issues',
      'has_projects', 'has_wiki', 'is_template', 'default_branch', 'allow_squash_merge',
      'allow_merge_commit', 'allow_rebase_merge', 'delete_branch_on_merge'

    Returns a JSON string containing the updated repository information.
    """
    try:
        api = _setup()
        owner, repo = repo_full_name.split('/')
        
        result = api.repos.update(owner=owner, repo=repo, **kwargs)
        return json.dumps({
            "name": result.name,
            "full_name": result.full_name,
            "description": result.description,
            "private": result.private,
            "default_branch": result.default_branch
        })
    except Exception as e:
        return f"Error: {str(e)}"