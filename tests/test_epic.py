from __future__ import annotations

import json
from pathlib import Path

import pytest

from discord_free_game_notifier.epic import EpicGameElement
from discord_free_game_notifier.epic import EpicGamesResponse
from discord_free_game_notifier.epic import Price
from discord_free_game_notifier.epic import TotalPrice
from discord_free_game_notifier.epic import if_mystery_game


@pytest.fixture
def base_price() -> Price:
    """Fixture for basic price structure.

    Returns:
        A Price object with zero values for all price fields.
    """
    return Price(totalPrice=TotalPrice(discountPrice=0, originalPrice=0, voucherDiscount=0, discount=0, currencyCode="USD"))


def test_if_mystery_game_with_mystery_game_title(base_price: Price) -> None:
    """Test that a game with 'Mystery Game' title is identified as mystery game."""
    game = EpicGameElement(title="Mystery Game", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is True


def test_if_mystery_game_with_mystery_game_lowercase(base_price: Price) -> None:
    """Test that a game with 'mystery game' (lowercase) title is identified as mystery game."""
    game = EpicGameElement(title="mystery game", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is True


def test_if_mystery_game_with_mystery_game_mixed_case(base_price: Price) -> None:
    """Test that a game with 'MyStErY gAmE' (mixed case) title is identified as mystery game."""
    game = EpicGameElement(title="MyStErY gAmE", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is True


def test_if_mystery_game_with_mystery_game_prefix(base_price: Price) -> None:
    """Test that a game with title starting with 'Mystery Game' is identified as mystery game."""
    game = EpicGameElement(title="Mystery Game: The Adventure", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is True


def test_if_mystery_game_with_regular_game(base_price: Price) -> None:
    """Test that a regular game is not identified as mystery game."""
    game = EpicGameElement(title="Grand Theft Auto V", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is False


def test_if_mystery_game_with_mystery_in_middle(base_price: Price) -> None:
    """Test that a game with 'mystery game' not at the start is not identified as mystery game."""
    game = EpicGameElement(title="The Mystery Game Collection", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is False


def test_if_mystery_game_with_empty_title(base_price: Price) -> None:
    """Test that a game with empty title is not identified as mystery game."""
    game = EpicGameElement(title="", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is False


def test_if_mystery_game_with_partial_match(base_price: Price) -> None:
    """Test that a game with 'Mystery' but not 'Mystery Game' is not identified as mystery game."""
    game = EpicGameElement(title="Mystery Island", id="test-id", status="ACTIVE", price=base_price)
    assert if_mystery_game(game) is False


def test_parse_search_endpoint_response() -> None:
    """Test that the search endpoint response (with DLCs) can be properly parsed."""
    # Load the test data
    test_file: Path = Path(__file__).parent / "epic_search_with_dlc.json"
    with test_file.open(encoding="utf-8") as f:
        json_data = json.load(f)

    # Parse the response
    response: EpicGamesResponse = EpicGamesResponse.model_validate(json_data)

    # Verify the response structure
    assert response.data is not None
    assert response.data.Catalog is not None
    assert response.data.Catalog.searchStore is not None
    assert len(response.data.Catalog.searchStore.elements) == 5

    # Verify the first element (DLC)
    dlc: EpicGameElement = response.data.Catalog.searchStore.elements[0]
    assert dlc.title == "Train Sim World® 6: Spirit of Steam: Liverpool Lime Street - Crewe"
    assert dlc.id == "c09a8ee4c3f7425fa1b9cda29372c901"
    assert dlc.price.totalPrice.originalPrice == 33900
    # DLC should have "addons" in categories
    assert any(cat.path == "addons" for cat in dlc.categories)

    # Verify a regular game (Paradise Killer)
    game: EpicGameElement = response.data.Catalog.searchStore.elements[1]
    assert game.title == "Paradise Killer"
    assert game.id == "c8a6d95c091b4fe0be8fdfb53216f942"
    assert game.price.totalPrice.originalPrice == 16900
    # Game should have "games" in categories
    assert any(cat.path == "games" for cat in game.categories)

    # Verify all elements have required price information
    for element in response.data.Catalog.searchStore.elements:
        assert element.price is not None
        assert element.price.totalPrice is not None
        assert element.price.totalPrice.discountPrice is not None
        assert element.price.totalPrice.originalPrice is not None
