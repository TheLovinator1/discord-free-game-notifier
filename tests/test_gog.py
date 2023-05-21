from discord_free_game_notifier.gog import get_game_name


def test_get_game_name() -> None:
    """Test if we can get the game name from the banner title."""
    game_name: str = get_game_name(
        banner_title_text="Thanks for being with us! Claim Left 4 Dead 3 as a token of our gratitude!",
    )
    assert game_name == "Left 4 Dead 3"

    broken_game_name: str = get_game_name(banner_title_text="yo")
    assert broken_game_name == "GOG Giveaway"
