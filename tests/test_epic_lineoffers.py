"""Test Epic Games lineOffers handling for DLCs."""

from __future__ import annotations

import calendar
import datetime
import json
import time
from pathlib import Path

import pytest
import pytz

from discord_free_game_notifier.epic import EpicGameElement
from discord_free_game_notifier.epic import EpicGamesResponse
from discord_free_game_notifier.epic import promotion_end
from discord_free_game_notifier.epic import promotion_start


@pytest.fixture
def dlc_response() -> EpicGamesResponse:
    """Load the test response with DLC that has lineOffers.

    Returns:
        EpicGamesResponse: Parsed test response containing DLC data.
    """
    test_file: Path = Path(__file__).parent / "epic_search_with_dlc.json"
    with test_file.open(encoding="utf-8") as f:
        data: dict[str, object] = json.load(f)
    return EpicGamesResponse.model_validate(data)


def test_dlc_with_lineoffers_end_date(dlc_response: EpicGamesResponse) -> None:
    """Test that DLC with lineOffers appliedRules gets correct end date."""
    # Get the Train Sim World DLC (first element)
    dlc: EpicGameElement = dlc_response.data.Catalog.searchStore.elements[0]
    assert dlc.title == "Train Sim World® 6: Spirit of Steam: Liverpool Lime Street - Crewe"

    # Check that it's free
    assert dlc.price.totalPrice.discountPrice == 0
    assert dlc.price.totalPrice.originalPrice > 0

    # Check that lineOffers exist and have an end date
    assert len(dlc.price.lineOffers) > 0
    assert len(dlc.price.lineOffers[0].appliedRules) > 0
    assert dlc.price.lineOffers[0].appliedRules[0].endDate == "2026-01-05T18:00:00.000Z"

    # Get promotion end date - should not be 0 anymore
    end_date: int = promotion_end(dlc)
    assert end_date != 0, "End date should be extracted from lineOffers"

    # The expected unix timestamp for 2026-01-05T18:00:00.000Z
    # Using Python's calendar.timegm for verification
    expected = int(calendar.timegm(time.strptime("2026-01-05T18:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")))
    assert end_date == expected


def test_dlc_with_lineoffers_no_start_date(dlc_response: EpicGamesResponse) -> None:
    """Test that DLC with lineOffers but no startDate uses current time."""
    dlc: EpicGameElement = dlc_response.data.Catalog.searchStore.elements[0]

    # The test data doesn't have startDate in lineOffers, but has an end date
    # So it should return the current timestamp
    start_date: int = promotion_start(dlc)
    current_time: int = round(datetime.datetime.now(tz=pytz.UTC).timestamp())

    # Should be close to current time (within a few seconds)
    assert start_date != 0, "Start date should not be 0 when there's an end date but no start date"
    assert abs(start_date - current_time) < 5, "Start date should be approximately current time"


def test_regular_game_still_works(dlc_response: EpicGamesResponse) -> None:
    """Test that regular games without lineOffers still work."""
    # Paradise Killer (second element) doesn't have lineOffers promotions
    game: EpicGameElement = dlc_response.data.Catalog.searchStore.elements[1]
    assert game.title == "Paradise Killer"

    # Should still work for regular games
    end_date: int = promotion_end(game)
    start_date: int = promotion_start(game)

    # These might be 0 if no promotions, but shouldn't error
    assert isinstance(end_date, int)
    assert isinstance(start_date, int)
