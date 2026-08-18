"""Tests for APScheduler integration."""

from __future__ import annotations

import datetime
import time
from collections.abc import Callable
from typing import TYPE_CHECKING
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

if TYPE_CHECKING:
    from apscheduler.job import Job


def test_scheduler_imports() -> None:
    """Test that APScheduler imports work correctly.

    This test will fail if the API changes in a way that breaks imports.
    """
    assert BlockingScheduler is not None, "Expected BlockingScheduler to be importable"
    assert JobExecutionEvent is not None, "Expected JobExecutionEvent to be importable"
    assert EVENT_JOB_ERROR is not None, "Expected EVENT_JOB_ERROR to be importable"
    assert EVENT_JOB_EXECUTED is not None, "Expected EVENT_JOB_EXECUTED to be importable"


def test_scheduler_initialization() -> None:
    """Test that BlockingScheduler can be instantiated."""
    scheduler = BlockingScheduler()
    assert scheduler is not None, f"Expected BlockingScheduler instance, got {type(scheduler)}"
    # Scheduler doesn't need to be shut down if never started


def test_add_listener() -> None:
    """Test that event listeners can be added with proper event masks."""
    scheduler = BlockingScheduler()
    scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    # If this doesn't raise, the API is compatible


def test_add_job_with_cron_trigger() -> None:
    """Test that jobs can be added with cron trigger and next_run_time using specific minutes."""
    scheduler = BlockingScheduler()

    job: Job = scheduler.add_job(
        check_free_games,
        "cron",
        minute="1,16,31,46",
        replace_existing=True,
        next_run_time=datetime.datetime.now(tz=datetime.UTC),
    )

    assert job is not None, f"Expected Job instance, got {type(job)}"
    assert job.func == check_free_games, f"Expected job function to be check_free_games, got {job.func}"


@patch("discord_free_game_notifier.main._safe_check_service", spec_set=Callable)
def test_job_execution_in_background(mock_safe_check: Mock) -> None:
    """Test that scheduled jobs can execute in background scheduler."""
    scheduler = BackgroundScheduler()

    try:
        scheduler.add_job(check_free_games, "interval", seconds=1, max_instances=1)

        scheduler.start()
        time.sleep(2.5)  # Wait for job to run at least twice

        assert mock_safe_check.called, "Expected _safe_check_service to be called, but it was not"

        assert_msg: str = f"Expected _safe_check_service to be called at least twice, but got {mock_safe_check.call_count}"
        assert mock_safe_check.call_count >= 2, assert_msg
    finally:
        scheduler.shutdown(wait=True)


def test_listener_with_successful_event() -> None:
    """Test the listener function handles successful events correctly."""
    mock_event = Mock(spec=JobExecutionEvent)
    mock_event.exception = None

    # Should not raise or log error
    my_listener(mock_event)


def test_listener_with_failed_event() -> None:
    """Test the listener function handles failed events correctly."""
    mock_event = Mock()
    mock_event.exception = Exception("Test error")

    # Should not raise, but will log error
    my_listener(mock_event)


def test_scheduler_shutdown_gracefully() -> None:
    """Test that scheduler can be shut down gracefully."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_free_games, "interval", seconds=60)
    scheduler.start()

    # Shutdown should not raise
    scheduler.shutdown(wait=True)


def test_cron_trigger_parameters() -> None:
    """Test that cron trigger accepts expected parameters with custom minute list."""
    scheduler = BlockingScheduler()

    # Test various cron parameters to ensure API compatibility
    job: Job = scheduler.add_job(
        check_free_games,
        "cron",
        minute="1,16,31,46",
        hour="*",
        replace_existing=True,
    )
    assert job is not None


def test_apscheduler_version_exists() -> None:
    """Test that APScheduler version can be determined."""
    assert hasattr(apscheduler, "__version__")
    assert isinstance(apscheduler.__version__, str)
    # Should be version 3.x (update this if you upgrade)
    assert apscheduler.__version__.startswith("3.")
