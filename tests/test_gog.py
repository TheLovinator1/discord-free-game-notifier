from __future__ import annotations

from collections.abc import Generator
from typing import Any

from discord_webhook import DiscordEmbed

from discord_free_game_notifier.gog import (
    get_free_gog_game,
    get_free_gog_game_from_store,
    get_game_name,
)


def test_get_game_name() -> None:
    """Test if we can get the game name from the banner title."""
    game_name: str = get_game_name(
        banner_title_text="Thanks for being with us! Claim Left 4 Dead 3 as a token of our gratitude!",
    )
    assert game_name == "Left 4 Dead 3"

    broken_game_name: str = get_game_name(banner_title_text="yo")
    assert broken_game_name == "GOG Giveaway"


def test_get_free_gog_game() -> None:
    """Test if we can get the free game from GOG."""
    get_free_gog_game()


# Define the test.
def test_get_free_gog_game_from_list() -> None:
    """Test if we can get the free game from GOG."""
    free_game: Generator[DiscordEmbed | None, Any, None] = get_free_gog_game_from_store()

    # Make sure we get a generator.
    assert free_game is not None
    assert isinstance(free_game, Generator)

    # Loop through the generator.
    for game in free_game:
        assert isinstance(game, DiscordEmbed)

        if game.author is None:
            # If the author is None, we can't do any tests.
            msg = "Author is None."
            raise AssertionError(msg)

        if game.image is None:
            # If the image is None, we can't do any tests.
            msg = "Image is None."
            raise AssertionError(msg)

        if game.description is None:
            # If the image is None, we can't do any tests.
            msg = "Image is None."
            raise AssertionError(msg)

        assert game.author["name"]
        assert game.author["icon_url"]
        assert game.author["url"]
        assert game.image["url"]
        assert game.description.startswith("[Click here to claim")

        # Stop the generator.
        break
