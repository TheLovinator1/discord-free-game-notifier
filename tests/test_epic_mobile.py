"""Tests for the epic_mobile module."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from discord_webhook import DiscordEmbed
from pydantic import HttpUrl
from pydantic import ValidationError

from discord_free_game_notifier.epic_mobile import EpicMobileGame
from discord_free_game_notifier.epic_mobile import get_epic_mobile_free_games


def test_epic_mobile_game_model() -> None:
    """Test creating an EpicMobileGame model."""
    game = EpicMobileGame(
        id="test_game",
        game_name="Test Mobile Game",
        game_url=HttpUrl("https://www.epicgames.com/en-US/p/test-game"),
        start_date=datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2025, 12, 31, 23, 59, 59, tzinfo=datetime.UTC),
        image_link=HttpUrl("https://example.com/image.jpg"),
        description="Test description",
        developer="Test Developer",
        platform="Android & iOS",
    )

    assert game.id == "test_game"
    assert game.game_name == "Test Mobile Game"
    assert game.platform == "Android & iOS"


def test_epic_mobile_game_platform_validation() -> None:
    """Test that platform validation works."""
    with pytest.raises(ValidationError):
        EpicMobileGame(
            id="test_game",
            game_name="Test Game",
            game_url=HttpUrl("https://www.epicgames.com/en-US/p/test"),
            start_date=datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2025, 12, 31, 23, 59, 59, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/image.jpg"),
            description="Test description",
            developer="Test Developer",
            platform="Windows",  # Invalid platform
        )


@patch("discord_free_game_notifier.epic_mobile.httpx.Client")
def test_get_epic_mobile_free_games_success(mock_client: MagicMock) -> None:
    """Test successfully fetching mobile games from JSON."""
    # Mock response
    mock_response = MagicMock()
    mock_response.is_error = False
    mock_response.json.return_value = {
        "free_games": [
            {
                "id": "test_mobile_game",
                "game_name": "Test Mobile Game",
                "game_url": "https://www.epicgames.com/en-US/p/test",
                "start_date": "2025-01-01T00:00:00+00:00",
                "end_date": "2025-12-31T23:59:59+00:00",
                "image_link": "https://example.com/image.jpg",
                "description": "Test description",
                "developer": "Test Developer",
                "platform": "Android",
            },
        ],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    with patch("discord_free_game_notifier.epic_mobile.already_posted", return_value=False):
        result = get_epic_mobile_free_games()

    assert result is not None
    assert len(result) == 1
    embed, game_id = result[0]
    assert isinstance(embed, DiscordEmbed)
    assert game_id == "test_mobile_game"


@patch("discord_free_game_notifier.epic_mobile.httpx.Client")
def test_get_epic_mobile_free_games_already_posted(mock_client: MagicMock) -> None:
    """Test that already posted games are skipped."""
    mock_response = MagicMock()
    mock_response.is_error = False
    mock_response.json.return_value = {
        "free_games": [
            {
                "id": "test_mobile_game",
                "game_name": "Test Mobile Game",
                "game_url": "https://www.epicgames.com/en-US/p/test",
                "start_date": "2025-01-01T00:00:00+00:00",
                "end_date": "2025-12-31T23:59:59+00:00",
                "image_link": "https://example.com/image.jpg",
                "description": "Test description",
                "developer": "Test Developer",
                "platform": "Android",
            },
        ],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    with patch("discord_free_game_notifier.epic_mobile.already_posted", return_value=True):
        result = get_epic_mobile_free_games()

    assert result is not None
    assert len(result) == 0


@patch("discord_free_game_notifier.epic_mobile.httpx.Client")
def test_get_epic_mobile_free_games_expired(mock_client: MagicMock) -> None:
    """Test that expired games are skipped."""
    mock_response = MagicMock()
    mock_response.is_error = False
    mock_response.json.return_value = {
        "free_games": [
            {
                "id": "expired_game",
                "game_name": "Expired Game",
                "game_url": "https://www.epicgames.com/en-US/p/expired",
                "start_date": "2020-01-01T00:00:00+00:00",
                "end_date": "2020-12-31T23:59:59+00:00",
                "image_link": "https://example.com/image.jpg",
                "description": "Expired game",
                "developer": "Test Developer",
                "platform": "iOS",
            },
        ],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    with patch("discord_free_game_notifier.epic_mobile.already_posted", return_value=False):
        result = get_epic_mobile_free_games()

    assert result is not None
    assert len(result) == 0


@patch("discord_free_game_notifier.epic_mobile.httpx.Client")
def test_get_epic_mobile_free_games_http_error(mock_client: MagicMock) -> None:
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.is_error = True
    mock_response.status_code = 404
    mock_response.reason_phrase = "Not Found"

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    result = get_epic_mobile_free_games()

    assert result is None
