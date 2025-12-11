from __future__ import annotations

import pytest

from discord_free_game_notifier.epic import EpicGameElement
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
