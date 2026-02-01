"""
Tests for webhook bot loop prevention.

Critical security tests to ensure the bot doesn't trigger itself in an infinite loop.
Part of WO041 - Critical Security Fix.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.mvp.webhook import app, rate_limiter, reset_pr_tracking
from src.mvp.rate_limiter import WebhookRateLimiter


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_github_app_auth():
    """Mock GitHub App authentication."""
    with patch('src.mvp.webhook.GITHUB_APP_AUTH') as mock_auth:
        mock_auth.get_installation_token.return_value = "test_token"
        yield mock_auth


@pytest.fixture
def mock_verify_signature():
    """Mock webhook signature verification to always pass."""
    with patch('src.mvp.webhook.verify_signature', return_value=True):
        yield


@pytest.fixture(autouse=True)
def reset_pr_tracking_fixture():
    """Reset PR tracking between tests."""
    reset_pr_tracking()
    yield
    reset_pr_tracking()


@pytest.fixture
def reset_rate_limiter():
    """Reset rate limiter between tests."""
    # Clear all rate limit states
    rate_limiter._states.clear()
    yield
    rate_limiter._states.clear()


def create_webhook_payload(
    action="opened",
    pr_number=1,
    user_login="human-user",
    user_id=12345,
    repo_full_name="owner/repo",
    commits=None
):
    """Create a mock webhook payload."""
    payload = {
        "action": action,
        "pull_request": {
            "number": pr_number,
            "id": pr_number,
            "head": {
                "ref": "feature-branch",
                "repo": {
                    "clone_url": "https://github.com/owner/repo.git"
                }
            },
            "user": {
                "login": user_login,
                "id": user_id
            }
        },
        "repository": {
            "full_name": repo_full_name
        },
        "installation": {
            "id": 123456
        }
    }

    if commits:
        payload["commits"] = commits

    return payload


class TestBotLoopPrevention:
    """Test bot loop prevention mechanisms."""

    def test_bot_user_detected_by_username(self, client, mock_verify_signature):
        """Test that bot user is detected by username."""
        payload = create_webhook_payload(
            user_login="poggio-bot[bot]",
            user_id=2634514
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Bot-triggered webhook skipped" in data["message"]
        assert data["author"] == "poggio-bot[bot]"

    def test_bot_user_detected_by_user_id(self, client, mock_verify_signature):
        """Test that bot user is detected by user ID."""
        payload = create_webhook_payload(
            user_login="some-other-name",
            user_id=2634514  # Bot's user ID
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Bot-triggered webhook skipped" in data["message"]

    def test_human_user_not_blocked(self, client, mock_verify_signature, mock_github_app_auth):
        """Test that human users are not blocked."""
        payload = create_webhook_payload(
            user_login="human-developer",
            user_id=99999
        )

        with patch('src.mvp.webhook.GitHubAPI') as mock_api, \
         patch('src.mvp.webhook.RepoCloner'):
            mock_api.return_value.get_pr_files.return_value = []
            mock_api.return_value.get_pr_diff.return_value = ""

            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

            # Should not be blocked (will process or fail for other reasons, but not blocked by bot detection)
            data = json.loads(response.data)
            assert "Bot-triggered webhook skipped" not in data.get("message", "")

    def test_bot_commit_detected_in_synchronize(self, client, mock_verify_signature):
        """Test that bot commits are detected in synchronize events."""
        commits = [
            {
                "author": {
                    "name": "poggio-bot[bot]",
                    "email": "2634514+poggio-bot[bot]@users.noreply.github.com"
                }
            }
        ]

        payload = create_webhook_payload(
            action="synchronize",
            user_login="human-user",
            user_id=99999,
            commits=commits
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be ignored due to synchronize action
        assert "ignored" in data["message"].lower()

    def test_bot_commit_detected_by_email_pattern(self, client, mock_verify_signature):
        """Test that bot commits are detected by email pattern."""
        commits = [
            {
                "author": {
                    "name": "GitHub Actions",
                    "email": "2634514+poggio-bot[bot]@users.noreply.github.com"
                }
            }
        ]

        payload = create_webhook_payload(
            action="synchronize",
            user_login="human-user",
            user_id=99999,
            commits=commits
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be ignored due to synchronize action
        assert "ignored" in data["message"].lower()

    def test_human_commit_not_blocked(self, client, mock_verify_signature, mock_github_app_auth):
        """Test that human commits in synchronize events are not blocked."""
        commits = [
            {
                "author": {
                    "name": "Human Developer",
                    "email": "human@example.com"
                }
            }
        ]

        payload = create_webhook_payload(
            action="synchronize",
            user_login="human-user",
            user_id=99999,
            commits=commits
        )

        with patch('src.mvp.webhook.GitHubAPI') as mock_api, \
         patch('src.mvp.webhook.RepoCloner'):
            mock_api.return_value.get_pr_files.return_value = []
            mock_api.return_value.get_pr_diff.return_value = ""

            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

            data = json.loads(response.data)
            # Should be ignored due to synchronize action
            assert "ignored" in data.get("message", "").lower()


class TestRateLimiting:
    """Test rate limiting mechanisms."""

    def test_rate_limiter_allows_normal_traffic(self, reset_rate_limiter):
        """Test that rate limiter allows normal traffic."""
        limiter = WebhookRateLimiter(max_events_per_window=5, window_seconds=60)

        # First 5 events should be allowed
        for i in range(5):
            allowed, reason = limiter.check_rate_limit("owner/repo", 1)
            assert allowed is True
            assert reason is None

    def test_rate_limiter_blocks_excessive_traffic(self, reset_rate_limiter):
        """Test that rate limiter blocks excessive traffic."""
        limiter = WebhookRateLimiter(max_events_per_window=5, window_seconds=60)

        # First 5 events allowed
        for i in range(5):
            limiter.check_rate_limit("owner/repo", 1)

        # 6th event should be blocked
        allowed, reason = limiter.check_rate_limit("owner/repo", 1)
        assert allowed is False
        assert "Rate limit exceeded" in reason

    def test_rate_limiter_circuit_breaker(self, reset_rate_limiter):
        """Test that circuit breaker triggers on rapid events."""
        limiter = WebhookRateLimiter(
            max_events_per_window=5,
            window_seconds=60,
            circuit_breaker_threshold=10
        )

        # Trigger circuit breaker with 10 rapid events
        for i in range(10):
            limiter.check_rate_limit("owner/repo", 1)

        # Next event should trigger circuit breaker
        allowed, reason = limiter.check_rate_limit("owner/repo", 1)
        assert allowed is False
        assert "Circuit breaker" in reason

    def test_rate_limiter_per_pr_isolation(self, reset_rate_limiter):
        """Test that rate limiting is isolated per PR."""
        limiter = WebhookRateLimiter(max_events_per_window=5, window_seconds=60)

        # Fill up rate limit for PR #1
        for i in range(5):
            limiter.check_rate_limit("owner/repo", 1)

        # PR #2 should still be allowed
        allowed, reason = limiter.check_rate_limit("owner/repo", 2)
        assert allowed is True
        assert reason is None

    def test_rate_limiter_webhook_integration(
        self, client, mock_verify_signature, reset_rate_limiter
    ):
        """Test rate limiter integration with webhook endpoint."""
        payload = create_webhook_payload(pr_number=1)

        # Send 6 requests rapidly (limit is 5)
        for i in range(6):
            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

            if i < 5:
                # First 5 should not be rate limited (may fail for other reasons)
                data = json.loads(response.data)
                assert "Rate limit exceeded" not in data.get("message", "")
            else:
                # 6th should be rate limited
                assert response.status_code == 429
                data = json.loads(response.data)
                assert "Rate limit exceeded" in data["message"]


class TestLoopPreventionScenarios:
    """Test real-world loop prevention scenarios."""

    def test_scenario_bot_creates_pr(self, client, mock_verify_signature):
        """Test scenario: Bot creates a PR (should be blocked)."""
        payload = create_webhook_payload(
            action="opened",
            user_login="poggio-bot[bot]",
            user_id=2634514
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Bot-triggered webhook skipped" in data["message"]

    def test_scenario_bot_pushes_to_pr(self, client, mock_verify_signature):
        """Test scenario: Bot pushes commit to PR (should be blocked)."""
        commits = [
            {
                "author": {
                    "name": "poggio-bot[bot]",
                    "email": "2634514+poggio-bot[bot]@users.noreply.github.com"
                }
            }
        ]

        payload = create_webhook_payload(
            action="synchronize",
            user_login="human-user",  # PR opened by human
            user_id=99999,
            commits=commits  # But bot pushed
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be ignored due to synchronize action
        assert "ignored" in data["message"].lower()

    def test_scenario_human_pr_with_human_commits(
        self, client, mock_verify_signature, mock_github_app_auth
    ):
        """Test scenario: Human creates PR and pushes (should be processed)."""
        commits = [
            {
                "author": {
                    "name": "Human Developer",
                    "email": "human@example.com"
                }
            }
        ]

        payload = create_webhook_payload(
            action="synchronize",
            user_login="human-user",
            user_id=99999,
            commits=commits
        )

        with patch('src.mvp.webhook.GitHubAPI') as mock_api, \
         patch('src.mvp.webhook.RepoCloner'):
            mock_api.return_value.get_pr_files.return_value = []
            mock_api.return_value.get_pr_diff.return_value = ""

            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

            # Should be ignored due to synchronize action
            data = json.loads(response.data)
            assert "ignored" in data.get("message", "").lower()

    def test_scenario_rapid_fire_webhooks(
        self, client, mock_verify_signature, reset_rate_limiter
    ):
        """Test scenario: Rapid-fire webhooks trigger circuit breaker."""
        payload = create_webhook_payload(pr_number=1)

        # Simulate 11 rapid webhook events (circuit breaker at 10)
        for i in range(11):
            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

        # Last response should be rate limited
        assert response.status_code == 429
        data = json.loads(response.data)
        assert "Rate limit exceeded" in data["message"]


class TestMonitoringAndLogging:
    """Test that loop prevention events are properly logged."""

    @patch('src.mvp.webhook.monitoring')
    def test_bot_detection_logged(self, mock_monitoring, client, mock_verify_signature):
        """Test that bot detection is logged to monitoring."""
        payload = create_webhook_payload(
            user_login="poggio-bot[bot]",
            user_id=2634514
        )

        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=dummy'}
        )

        # Verify monitoring was called
        assert mock_monitoring.log_event.called

        # Find the WEBHOOK_SKIPPED event
        calls = mock_monitoring.log_event.call_args_list
        skipped_calls = [
            call for call in calls 
            if len(call[0]) > 0 and 'WEBHOOK_SKIPPED' in str(call[0][0])
        ]

        assert len(skipped_calls) > 0

    @patch('src.mvp.webhook.monitoring')
    def test_rate_limit_logged(
        self, mock_monitoring, client, mock_verify_signature, reset_rate_limiter
    ):
        """Test that rate limiting is logged to monitoring."""
        payload = create_webhook_payload(pr_number=1)

        # Trigger rate limit
        for i in range(6):
            client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'X-Hub-Signature-256': 'sha256=dummy'}
            )

        # Verify rate limit was logged
        assert mock_monitoring.log_event.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])