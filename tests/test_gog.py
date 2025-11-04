"""Tests for GOG free game checker."""

from pathlib import Path

from bs4 import BeautifulSoup
from bs4 import Tag

from discord_free_game_notifier.gog import get_game_image
from discord_free_game_notifier.gog import get_game_name
from discord_free_game_notifier.gog import get_giveaway_link


def test_gog_has_game_on_index_page() -> None:
    """Test that we can detect a game on the GOG index page."""
    # Load the test HTML file with a giveaway
    test_file: Path = Path(__file__).parent / "gog_has_games.html"
    html_content: str = test_file.read_text(encoding="utf-8")

    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")
    giveaway: Tag | None = soup.find("giveaway")

    # Assert that we found a giveaway
    assert giveaway is not None, "Expected to find a giveaway tag in gog_has_games.html"

    # Parse the giveaway content
    giveaway_soup = BeautifulSoup(str(giveaway), "html.parser")

    # Test game name extraction
    game_name: str = get_game_name(giveaway_soup=giveaway_soup, giveaway=giveaway)
    assert game_name == "STASIS", f"Expected game name 'STASIS', got '{game_name}'"

    # Test giveaway link extraction
    giveaway_link: str = get_giveaway_link(giveaway=giveaway, game_name=game_name)
    assert giveaway_link == "https://www.gog.com/en/game/stasis", f"Expected 'https://www.gog.com/en/game/stasis', got '{giveaway_link}'"

    # Test image URL extraction
    image_url: str = get_game_image(giveaway=giveaway_soup, game_name=game_name)
    assert image_url is not None, "Expected to find an image URL"

    # Note: The saved HTML file has relative paths, so we just check it's not empty
    # In real usage from the live site, this would be an absolute URL
    assert len(image_url) > 0, "Expected a non-empty image URL"


def test_gog_no_game_on_index_page() -> None:
    """Test that we correctly handle no giveaway on the GOG index page."""
    # Load the test HTML file without a giveaway
    test_file: Path = Path(__file__).parent / "gog_no_games.html"
    html_content: str = test_file.read_text(encoding="utf-8")

    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")
    giveaway: Tag | None = soup.find("giveaway")

    # Assert that we did not find a giveaway
    assert giveaway is None, "Expected no giveaway tag in gog_no_games.html"
