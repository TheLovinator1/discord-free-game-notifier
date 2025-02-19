import html
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import ParseResult, parse_qs, urlparse

import pytest
import requests

from discord_free_game_notifier import settings
from discord_free_game_notifier.steam import STEAM_URL, get_free_steam_games

if TYPE_CHECKING:
    from discord_webhook import DiscordEmbed


# A fake Response object to mimic requests.Response
class FakeResponse:
    """A mock Response class that mimics the behavior of requests.Response.

    This class is used for testing purposes to simulate HTTP responses without making actual HTTP requests.

    Attributes:
        text (str): The response body as text.
        status_code (int): The HTTP status code of the response.
        json_data (dict[str, dict[str, Any]]): The JSON data to be returned by json() method.

    Properties:
        ok (bool): Returns True if status_code is 200, False otherwise.

    Methods:
        json(): Returns the pre-set JSON data as a dictionary.
    """

    def __init__(self, text: str, status_code: int) -> None:
        """Initialize the FakeResponse object with the provided text and status code.

        Args:
            text (str): The response body as text.
            status_code (int): The HTTP status code of the response.
        """
        self.text: str = text
        self.status_code: int = status_code
        self.json_data: dict[str, dict[str, Any]] = {}

    @property
    def ok(self) -> bool:
        """Returns True if the status code is 200, False otherwise."""
        return self.status_code == 200  # noqa: PLR2004

    def json(self) -> dict[str, dict[str, Any]]:
        """Returns the pre-set JSON data as a dictionary."""
        return self.json_data


def fake_get(
    url: str,
    headers: dict[str, str] | None = None,  # noqa: ARG001
    timeout: int | None = None,  # noqa: ARG001
    *,
    empty_mode: bool = False,
    **kwargs: dict[str, Any],  # noqa: ARG001
) -> FakeResponse:
    """A fake requests.get function that returns local HTML for the Steam search page and fake JSON data for API calls.

    Args:
        url (str): The URL to fetch.
        headers (dict[str, str] | None): The headers to use for the request.
        timeout (int | None): The timeout for the request.
        empty_mode (bool): Flag to determine which HTML file to return.
        **kwargs (dict[str, Any]): Additional keyword arguments.

    Returns:
        FakeResponse: A fake Response object with the appropriate data for the given URL.
    """
    if url.startswith(STEAM_URL.split("?")[0]):
        # steam.html has 2 games, steam_empty.html has 0 games
        html_filename: Literal["Steam_empty.html", "Steam.html"] = "Steam_empty.html" if empty_mode else "Steam.html"
        html_path: Path = Path(__file__).parent / html_filename
        html_text: str = html_path.read_text(encoding="utf-8")
        return FakeResponse(html_text, 200)

    if url.startswith("https://store.steampowered.com/api/appdetails"):
        parsed: ParseResult = urlparse(url)
        query: dict[str, list[str]] = parse_qs(parsed.query)
        appids: list[str] = query.get("appids", ["753"])
        appid: str = appids[0]

        data: dict[str, dict[str, dict[str, str | list[str]]]] = {
            appid: {
                "data": {
                    "header_image": "http://example.com/header.jpg",
                    "short_description": "A free game description",
                    "developers": ["Developer A"],
                    "publishers": ["Publisher A"],
                },
            },
        }
        response = FakeResponse("", 200)
        response.json_data = data
        return response

    return FakeResponse("", 404)


@pytest.fixture
def patch_requests_get_with_mode(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Patch requests.get dynamically to return either Steam.html or Steam_empty.html.

    Args:
        monkeypatch (pytest.MonkeyPatch): The pytest monkeypatch object.

    Returns:
        Callable[[bool], None]: A function that can be called to patch requests.get with the specified mode (empty or not empty).
    """

    def _patch(*, empty_mode: bool = False) -> None:
        monkeypatch.setattr(requests, "get", lambda url, **kwargs: fake_get(url, empty_mode=empty_mode, **kwargs))  # pyright: ignore[ reportCallIssue ]

    return _patch


@pytest.fixture(autouse=True)
def use_temp_app_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Override the app_dir in settings to a temporary directory so that the tests do not interfere with any real data.

    Args:
        tmp_path (Path): The temporary path provided by pytest.
        monkeypatch (pytest.MonkeyPatch): The pytest monkeypatch object.
    """
    monkeypatch.setattr(settings, "app_dir", str(tmp_path))


@pytest.mark.parametrize("empty_mode", [False, True])
def test_get_free_steam_games(tmp_path: Path, patch_requests_get_with_mode: Callable[..., None], *, empty_mode: bool) -> None:
    """Test get_free_steam_games with both Steam.html and Steam_empty.html.

    Args:
        tmp_path (Path): The temporary path provided by pytest.
        patch_requests_get_with_mode: The fixture to patch requests.get.
        empty_mode (bool): Whether to use Steam_empty.html (True) or Steam.html (False).
    """
    patch_requests_get_with_mode(empty_mode=empty_mode)

    steam_txt: Path = tmp_path / "steam.txt"
    if steam_txt.exists():
        steam_txt.unlink()

    embeds = list(get_free_steam_games())

    if empty_mode:
        assert len(embeds) == 0, "Embeds should be empty when no free games are found"
    else:
        assert len(embeds) > 0, "No embeds were returned by get_free_steam_games()"

        # Check the first embed for expected properties.
        first_embed: DiscordEmbed = embeds[0]

        # Verify the author is set to "Steam".
        author: dict[str, str | None] | None = first_embed.author
        assert author, "Embed author is missing"
        assert "name" in author, "Embed author name is missing"
        assert "Steam" in (author.get("name") or ""), "Embed author does not contain 'Steam'"

        # Verify that the header image from our fake JSON is used.
        image: dict[str, str | int | None] | None = first_embed.image
        assert image, "Embed image is missing"
        assert "url" in image, "Embed image URL is missing"
        assert str(image.get("url", "")).startswith("http://example.com/header.jpg"), "Embed image URL not as expected"

        # If a description was set (via the short_description), verify it contains the expected text.
        if first_embed.description:
            description = html.unescape(first_embed.description)
            assert "free game description" in description.lower(), "Embed description does not contain expected text"

        # Check that a footer was set (with developer/publisher information).
        footer: dict[str, str | None] | None = first_embed.footer
        footer_text: str | None = footer.get("text", "") if footer is not None else ""
        assert footer, "Embed footer is missing"
        assert footer_text, "Embed footer text is missing"
        assert footer_text.strip(), "Embed footer is empty or missing"
