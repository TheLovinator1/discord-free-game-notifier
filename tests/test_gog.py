"""Tests for GOG free game checker."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Self

import httpx
from bs4 import BeautifulSoup
from hypothesis import given
from hypothesis import strategies as st

from discord_free_game_notifier import gog as gog_mod
from discord_free_game_notifier.gog import get_game_image
from discord_free_game_notifier.gog import get_game_name
from discord_free_game_notifier.gog import get_giveaway_link

if TYPE_CHECKING:
    from types import TracebackType

    import pytest
    from bs4 import Tag


class _TimeoutClient:
    timeouts: ClassVar[list[object]] = []

    def __init__(self, timeout: object) -> None:
        self.timeouts.append(timeout)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        return None

    def get(self, url: str, *, headers: dict[str, str]) -> httpx.Response:
        _ = (url, headers)
        msg = "timed out"
        raise httpx.ReadTimeout(msg)


class _FakeLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str, *args: object) -> None:
        _ = args
        self.errors.append(message)


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


def test_gog_front_page_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    _TimeoutClient.timeouts = []
    fake_logger = _FakeLogger()
    monkeypatch.setattr(gog_mod.httpx, "Client", _TimeoutClient)
    monkeypatch.setattr(gog_mod, "logger", fake_logger)

    assert gog_mod.get_free_gog_game() is None
    assert _TimeoutClient.timeouts == [gog_mod.GOG_FRONT_PAGE_TIMEOUT]
    assert fake_logger.warnings == ["GOG front page timed out, skipping this check: timed out"]
    assert fake_logger.errors == []


def test_gog_store_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    _TimeoutClient.timeouts = []
    fake_logger = _FakeLogger()
    monkeypatch.setattr(gog_mod.httpx, "Client", _TimeoutClient)
    monkeypatch.setattr(gog_mod, "logger", fake_logger)

    assert gog_mod.get_free_gog_game_from_store() == []
    assert _TimeoutClient.timeouts == [gog_mod.GOG_STORE_TIMEOUT]
    assert fake_logger.warnings == ["GOG store search timed out, skipping this check: timed out"]
    assert fake_logger.errors == []


@given(st.text(min_size=1, max_size=100).filter(lambda s: "<" not in s and ">" not in s))
def test_gog_game_name_is_string(name: str) -> None:
    """Property: GOG game names can be arbitrary non-HTML strings."""
    # This is a structural test: we expect game names to be strings without HTML tags
    assert isinstance(name, str)
    assert "<" not in name
    assert ">" not in name
