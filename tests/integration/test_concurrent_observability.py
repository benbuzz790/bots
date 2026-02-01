"""
Integration tests for per-bot observability functions.

Tests concurrent bot execution scenarios to ensure accurate cost and token tracking
when multiple bots run simultaneously.
"""

import threading
import time

import pytest

from bots.observability import metrics


@pytest.fixture(autouse=True)
def reset_metrics_before_test():
    """Reset metrics state before each test."""
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


def test_per_bot_token_tracking():
    """Test that tokens are tracked separately for each bot."""
    # Record tokens for bot_1
    metrics.record_tokens(
        input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    # Record tokens for bot_2
    metrics.record_tokens(
        input_tokens=200, output_tokens=75, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_2"
    )

    # Verify bot_1 tokens
    bot_1_tokens = metrics.get_bot_tokens("bot_1")
    assert bot_1_tokens["input"] == 100
    assert bot_1_tokens["output"] == 50
    assert bot_1_tokens["total"] == 150

    # Verify bot_2 tokens
    bot_2_tokens = metrics.get_bot_tokens("bot_2")
    assert bot_2_tokens["input"] == 200
    assert bot_2_tokens["output"] == 75
    assert bot_2_tokens["total"] == 275

    # Verify global tokens include both
    global_tokens = metrics.get_total_tokens(0.0)
    assert global_tokens["total"] == 425  # 150 + 275


def test_per_bot_cost_tracking():
    """Test that costs are tracked separately for each bot."""
    # Record cost for bot_1
    metrics.record_cost(cost=0.015, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1")

    # Record cost for bot_2
    metrics.record_cost(cost=0.025, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_2")

    # Verify bot_1 cost
    bot_1_cost = metrics.get_bot_cost("bot_1")
    assert abs(bot_1_cost - 0.015) < 0.0001

    # Verify bot_2 cost
    bot_2_cost = metrics.get_bot_cost("bot_2")
    assert abs(bot_2_cost - 0.025) < 0.0001

    # Verify global cost includes both
    global_cost = metrics.get_total_cost(0.0)
    assert abs(global_cost - 0.040) < 0.0001


def test_per_bot_timestamp_filtering():
    """Test that timestamp filtering works correctly for per-bot metrics."""
    # Get start time slightly before recording to ensure > comparison works
    start_time = time.time() - 0.001

    # Record some tokens for bot_1
    metrics.record_tokens(
        input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    time.sleep(0.01)  # Small delay
    checkpoint = time.time()
    time.sleep(0.01)

    # Record more tokens for bot_1
    metrics.record_tokens(
        input_tokens=200, output_tokens=75, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    # Get tokens since start (should include both)
    tokens_since_start = metrics.get_bot_tokens("bot_1", start_time)
    assert tokens_since_start["total"] == 425  # 150 + 275

    # Get tokens since checkpoint (should only include second recording)
    tokens_since_checkpoint = metrics.get_bot_tokens("bot_1", checkpoint)
    assert tokens_since_checkpoint["total"] == 275


def test_concurrent_bot_execution():
    """Test that concurrent bot executions don't interfere with each other."""
    results = {}
    errors = []

    def bot_worker(bot_id: str, num_calls: int):
        """Simulate a bot making multiple API calls."""
        try:
            for i in range(num_calls):
                # Record tokens
                metrics.record_tokens(
                    input_tokens=100 + i,
                    output_tokens=50 + i,
                    provider="anthropic",
                    model="claude-3-5-sonnet-latest",
                    bot_id=bot_id,
                )

                # Record cost
                metrics.record_cost(
                    cost=0.001 * (i + 1), provider="anthropic", model="claude-3-5-sonnet-latest", bot_id=bot_id
                )

                # Small delay to simulate real work
                time.sleep(0.001)

            # Store results
            results[bot_id] = {"tokens": metrics.get_bot_tokens(bot_id), "cost": metrics.get_bot_cost(bot_id)}
        except Exception as e:
            errors.append((bot_id, str(e)))

    # Create threads for 5 concurrent bots
    threads = []
    for i in range(5):
        bot_id = f"bot_{i}"
        thread = threading.Thread(target=bot_worker, args=(bot_id, 10))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all bots have results
    assert len(results) == 5

    # Verify each bot has independent metrics
    for i in range(5):
        bot_id = f"bot_{i}"
        assert bot_id in results

        # Each bot made 10 calls with increasing tokens
        # Call 0: 100+50=150, Call 1: 101+51=152, ..., Call 9: 109+59=168
        # Total = 150+152+154+156+158+160+162+164+166+168 = 1590
        expected_total = sum(100 + 50 + 2 * j for j in range(10))
        assert results[bot_id]["tokens"]["total"] == expected_total

        # Each bot made 10 calls with increasing costs
        # Call 0: 0.001, Call 1: 0.002, ..., Call 9: 0.010
        # Total = 0.001+0.002+...+0.010 = 0.055
        expected_cost = sum(0.001 * (j + 1) for j in range(10))
        assert abs(results[bot_id]["cost"] - expected_cost) < 0.0001


def test_clear_bot_metrics():
    """Test that clearing bot metrics works correctly."""
    # Record metrics for bot_1
    metrics.record_tokens(
        input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    metrics.record_cost(cost=0.015, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1")

    # Verify metrics exist
    assert metrics.get_bot_tokens("bot_1")["total"] == 150
    assert abs(metrics.get_bot_cost("bot_1") - 0.015) < 0.0001

    # Clear bot_1 metrics
    metrics.clear_bot_metrics("bot_1")

    # Verify metrics are cleared
    assert metrics.get_bot_tokens("bot_1")["total"] == 0
    assert metrics.get_bot_cost("bot_1") == 0.0


def test_get_all_bot_ids():
    """Test that get_all_bot_ids returns all tracked bots."""
    # Initially no bots
    assert len(metrics.get_all_bot_ids()) == 0

    # Record metrics for multiple bots
    for i in range(3):
        bot_id = f"bot_{i}"
        metrics.record_tokens(
            input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id=bot_id
        )

    # Verify all bot IDs are returned
    bot_ids = metrics.get_all_bot_ids()
    assert len(bot_ids) == 3
    assert "bot_0" in bot_ids
    assert "bot_1" in bot_ids
    assert "bot_2" in bot_ids


def test_get_and_clear_last_metrics_per_bot():
    """Test that get_and_clear_last_metrics works with bot_id parameter."""
    # Record metrics for bot_1
    metrics.record_tokens(
        input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    metrics.record_cost(cost=0.015, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1")

    # Get and clear bot_1 metrics
    last_metrics = metrics.get_and_clear_last_metrics(bot_id="bot_1")
    assert last_metrics["input_tokens"] == 100
    assert last_metrics["output_tokens"] == 50
    assert abs(last_metrics["cost"] - 0.015) < 0.0001

    # Verify metrics are cleared
    cleared_metrics = metrics.get_and_clear_last_metrics(bot_id="bot_1")
    assert cleared_metrics["input_tokens"] == 0
    assert cleared_metrics["output_tokens"] == 0
    assert cleared_metrics["cost"] == 0.0


def test_backward_compatibility_global_metrics():
    """Test that global metrics still work without bot_id (backward compatibility)."""
    # Record metrics without bot_id
    metrics.record_tokens(input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest")

    metrics.record_cost(cost=0.015, provider="anthropic", model="claude-3-5-sonnet-latest")

    # Verify global metrics work
    global_tokens = metrics.get_total_tokens(0.0)
    assert global_tokens["total"] == 150

    global_cost = metrics.get_total_cost(0.0)
    assert abs(global_cost - 0.015) < 0.0001

    # Verify get_and_clear_last_metrics works without bot_id
    last_metrics = metrics.get_and_clear_last_metrics()
    assert last_metrics["input_tokens"] == 100
    assert last_metrics["output_tokens"] == 50
    assert abs(last_metrics["cost"] - 0.015) < 0.0001


def test_mixed_global_and_per_bot_metrics():
    """Test that global and per-bot metrics can coexist."""
    # Record global metrics
    metrics.record_tokens(input_tokens=100, output_tokens=50, provider="anthropic", model="claude-3-5-sonnet-latest")

    # Record per-bot metrics
    metrics.record_tokens(
        input_tokens=200, output_tokens=75, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id="bot_1"
    )

    # Global metrics should include both
    global_tokens = metrics.get_total_tokens(0.0)
    assert global_tokens["total"] == 425  # 150 + 275

    # Per-bot metrics should only include bot_1
    bot_1_tokens = metrics.get_bot_tokens("bot_1")
    assert bot_1_tokens["total"] == 275

    # Non-existent bot should return zeros
    bot_2_tokens = metrics.get_bot_tokens("bot_2")
    assert bot_2_tokens["total"] == 0


def test_cached_tokens_per_bot():
    """Test that cached tokens are tracked correctly per bot."""
    # Record tokens with caching for bot_1
    metrics.record_tokens(
        input_tokens=100,
        output_tokens=50,
        cached_tokens=25,
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        bot_id="bot_1",
    )

    # Verify cached tokens are tracked
    bot_1_tokens = metrics.get_bot_tokens("bot_1")
    assert bot_1_tokens["input"] == 100
    assert bot_1_tokens["output"] == 50
    assert bot_1_tokens["cached"] == 25
    assert bot_1_tokens["total"] == 175


def test_thread_safety_stress():
    """Stress test thread safety with many concurrent operations."""
    num_threads = 20
    operations_per_thread = 50
    errors = []

    def stress_worker(worker_id: int):
        """Perform many rapid metric operations."""
        try:
            bot_id = f"stress_bot_{worker_id}"
            for i in range(operations_per_thread):
                metrics.record_tokens(
                    input_tokens=i, output_tokens=i, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id=bot_id
                )
                metrics.record_cost(cost=0.001, provider="anthropic", model="claude-3-5-sonnet-latest", bot_id=bot_id)
                # Query metrics frequently
                metrics.get_bot_tokens(bot_id)
                metrics.get_bot_cost(bot_id)
        except Exception as e:
            errors.append((worker_id, str(e)))

    # Create and start threads
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=stress_worker, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Verify no errors
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all bots are tracked
    bot_ids = metrics.get_all_bot_ids()
    assert len(bot_ids) == num_threads
