import pytest
import os
from unittest.mock import Mock, patch
from bots.tools.reddit_tools import (
    view_subreddit_posts,
    view_post_comments,
    post_comment,
    _get_reddit_instance
)

@pytest.fixture
def mock_env_no_auth():
    """Fixture to simulate environment with basic Reddit API credentials"""
    with patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'fake_client_id',
        'REDDIT_CLIENT_SECRET': 'fake_client_secret',
        'REDDIT_USER_AGENT': 'test_agent'
    }):
        yield

@pytest.fixture
def mock_env_with_auth():
    """Fixture to simulate environment with full Reddit API credentials"""
    with patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'fake_client_id',
        'REDDIT_CLIENT_SECRET': 'fake_client_secret',
        'REDDIT_USER_AGENT': 'test_agent',
        'REDDIT_USERNAME': 'fake_user',
        'REDDIT_PASSWORD': 'fake_pass'
    }):
        yield

@pytest.fixture
def mock_reddit():
    """Fixture to provide a mock Reddit instance"""
    with patch('praw.Reddit') as mock_reddit:
        mock_instance = Mock()
        mock_reddit.return_value = mock_instance
        yield mock_instance

def test_credentials_not_configured():
    """Test behavior when no credentials are configured"""
    with patch.dict(os.environ, clear=True):
        reddit, error = _get_reddit_instance()
        assert reddit is None
        assert "Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET" in error

def test_basic_credentials_configured(mock_env_no_auth, mock_reddit):
    """Test successful initialization with basic credentials"""
    reddit, error = _get_reddit_instance()
    assert reddit is not None
    assert error is None

def test_auth_credentials_configured(mock_env_with_auth, mock_reddit):
    """Test successful initialization with auth credentials"""
    reddit, error = _get_reddit_instance(need_auth=True)
    assert reddit is not None
    assert error is None

def test_view_subreddit_invalid_sort():
    """Test viewing subreddit with invalid sort parameter"""
    result = view_subreddit_posts('python', sort='invalid')
    assert "Invalid sort method" in result

def test_view_comments_invalid_sort():
    """Test viewing comments with invalid sort parameter"""
    result = view_post_comments('abc123', sort='invalid')
    assert "Invalid sort method" in result

@patch('praw.Reddit')
def test_view_subreddit_posts_success(mock_reddit_class, mock_env_no_auth):
    """Test successful subreddit posts viewing"""
    # Setup mock post
    mock_post = Mock()
    mock_post.title = "Test Post"
    mock_post.author = "test_user"
    mock_post.created_utc = 1600000000
    mock_post.score = 42
    mock_post.url = "https://reddit.com/r/test/123"
    mock_post.id = "abc123"

    # Setup mock Reddit instance
    mock_reddit = Mock()
    mock_reddit_class.return_value = mock_reddit
    mock_subreddit = Mock()
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_subreddit.hot.return_value = [mock_post]

    result = view_subreddit_posts('test', limit=1)
    assert "Test Post" in result
    assert "test_user" in result
    assert "abc123" in result

def test_actual_credentials():
    """
    Test if actual Reddit credentials are properly configured in the environment.
    This test helps users verify their setup.
    """
    reddit, error = _get_reddit_instance(need_auth=True)
    if error:
        print(f"\nDebug - Error from _get_reddit_instance: {error}")
        pytest.skip(f"Skipping test because: {error}")
    
    print("\nDebug - Successfully got Reddit instance, attempting to authenticate...")
    assert reddit is not None
    try:
        # Try to access Reddit API
        username = reddit.user.me().name
        print(f"Debug - Successfully authenticated as: u/{username}")
        assert True  # If we get here, credentials work
    except Exception as e:
        print(f"\nDebug - Authentication failed with error: {str(e)}")
        pytest.fail(f"Credentials configured but authentication failed: {str(e)}")
        print(f"\nDebug - Authentication failed with error: {str(e)}")
        pytest.fail(f"Credentials configured but authentication failed: {str(e)}")

if __name__ == '__main__':
    test_actual_credentials()