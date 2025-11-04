"""Tests for APScheduler integration."""

import datetime
import time
from unittest.mock import Mock
from unittest.mock import patch

import apscheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.events import JobExecutionEvent
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from discord_free_game_notifier.main import check_free_games
from discord_free_game_notifier.main import my_listener


def test_scheduler_imports():
    """Test that APScheduler imports work correctly.

    This test will fail if the API changes in a way that breaks imports.
    """
    assert BlockingScheduler is not None
    assert JobExecutionEvent is not None
    assert EVENT_JOB_ERROR is not None
    assert EVENT_JOB_EXECUTED is not None


def test_scheduler_initialization():
    """Test that BlockingScheduler can be instantiated."""
    scheduler = BlockingScheduler()
    assert scheduler is not None
    # Scheduler doesn't need to be shut down if never started


def test_add_listener():
    """Test that event listeners can be added with proper event masks."""
    scheduler = BlockingScheduler()
    scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    # If this doesn't raise, the API is compatible


def test_add_job_with_cron_trigger():
    """Test that jobs can be added with cron trigger and next_run_time."""
    scheduler = BlockingScheduler()

    job = scheduler.add_job(
        check_free_games,
        "cron",
        minute="*/15",
        replace_existing=True,
        next_run_time=datetime.datetime.now(tz=datetime.UTC),
    )

    assert job is not None
    assert job.func == check_free_games


@patch("discord_free_game_notifier.main._safe_check_service")
def test_job_execution_in_background(mock_safe_check: Mock) -> None:
    """Test that scheduled jobs can execute in background scheduler."""
    scheduler = BackgroundScheduler()

    try:
        scheduler.add_job(check_free_games, "interval", seconds=1, max_instances=1)

        scheduler.start()
        time.sleep(2.5)  # Wait for job to run at least twice

        assert mock_safe_check.called
        assert mock_safe_check.call_count >= 2
    finally:
        scheduler.shutdown(wait=True)


def test_listener_with_successful_event():
    """Test the listener function handles successful events correctly."""
    mock_event = Mock()
    mock_event.exception = None

    # Should not raise or log error
    my_listener(mock_event)


def test_listener_with_failed_event():
    """Test the listener function handles failed events correctly."""
    mock_event = Mock()
    mock_event.exception = Exception("Test error")

    # Should not raise, but will log error
    my_listener(mock_event)


def test_scheduler_shutdown_gracefully():
    """Test that scheduler can be shut down gracefully."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_free_games, "interval", seconds=60)
    scheduler.start()

    # Shutdown should not raise
    scheduler.shutdown(wait=True)


def test_cron_trigger_parameters():
    """Test that cron trigger accepts expected parameters."""
    scheduler = BlockingScheduler()

    # Test various cron parameters to ensure API compatibility
    job = scheduler.add_job(
        check_free_games,
        "cron",
        minute="*/15",
        hour="*",
        replace_existing=True,
    )
    assert job is not None


def test_apscheduler_version_exists():
    """Test that APScheduler version can be determined."""
    assert hasattr(apscheduler, "__version__")
    assert isinstance(apscheduler.__version__, str)
    # Should be version 3.x (update this if you upgrade)
    assert apscheduler.__version__.startswith("3.")
