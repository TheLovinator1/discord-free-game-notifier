"""Tests for Steam free game checker."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from bs4 import ResultSet
from bs4 import Tag

from discord_free_game_notifier.steam import AppDetailsData
from discord_free_game_notifier.steam import MoreData
from discord_free_game_notifier.steam import PriceOverview
from discord_free_game_notifier.steam import ReleaseDate


def test_steam_has_free_games() -> None:
    """Test that we can detect free games on Steam search results page."""
    # Load the test HTML file with free games
    test_file: Path = Path(__file__).parent / "Steam.html"
    html_content: str = test_file.read_text(encoding="utf-8")

    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all search result rows
    search_results: ResultSet[Tag] = soup.find_all("a", class_="search_result_row")

    # Assert that we found search results
    assert len(search_results) > 0, f"Expected to find search result rows in Steam.html, found {len(search_results)}"

    # Verify first game
    _verify_first_game(search_results[0])

    # Verify second game
    _verify_second_game(search_results[1])


def _verify_first_game(first_game: Tag) -> None:
    """Verify the first game has expected attributes."""
    # Verify it has the expected attributes
    assert first_game.has_attr("data-ds-appid"), "Expected search result to have data-ds-appid attribute"
    assert first_game["data-ds-appid"] == "1507530", f"Expected app ID '1507530', got '{first_game['data-ds-appid']}'"

    # Get the game title
    title_element: Tag | None = first_game.find("span", class_="title")
    assert title_element is not None, "Expected to find title element"
    expected_title = "Stellar Mess: The Princess Conundrum (Chapter 1)"
    assert title_element.text.strip() == expected_title, f"Expected '{expected_title}', got '{title_element.text.strip()}'"

    # Verify discount is 100% (free)
    discount_block: Tag | None = first_game.find("div", class_="discount_block")
    assert discount_block is not None, "Expected to find discount block"
    assert discount_block.has_attr("data-discount"), "Expected discount block to have data-discount attribute"
    assert discount_block["data-discount"] == "100", f"Expected 100% discount, got '{discount_block['data-discount']}%'"

    # Verify final price is 0
    assert discount_block.has_attr("data-price-final"), "Expected discount block to have data-price-final attribute"
    assert discount_block["data-price-final"] == "0", f"Expected final price to be '0', got '{discount_block['data-price-final']}'"


def _verify_second_game(second_game: Tag) -> None:
    """Verify the second game has expected attributes."""
    assert second_game["data-ds-appid"] == "3161090", f"Expected app ID '3161090', got '{second_game['data-ds-appid']}'"

    title_element: Tag | None = second_game.find("span", class_="title")
    assert title_element is not None, "Expected to find title element for second game"
    expected_title = "Royal Quest Online - Hero Power"
    assert title_element.text.strip() == expected_title, f"Expected '{expected_title}', got '{title_element.text.strip()}'"


def test_steam_no_free_games() -> None:
    """Test that we correctly handle no free games on Steam search results page."""
    # Load the test HTML file without free games
    test_file: Path = Path(__file__).parent / "Steam_empty.html"
    html_content: str = test_file.read_text(encoding="utf-8")

    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all search result rows
    search_results: ResultSet[Tag] = soup.find_all("a", class_="search_result_row")

    # Assert that we found no search results
    assert len(search_results) == 0, f"Expected no search result rows in Steam_empty.html, found {len(search_results)}"


def test_from_app_details_all_fields_mapped() -> None:
    data = AppDetailsData(
        developers=["Dev A", "Dev B"],
        publishers=["Pub X"],
        price_overview=PriceOverview(
            currency="EUR",
            initial=499,
            final=0,
            discount_percent=100,
            initial_formatted="4,99€",
            final_formatted="0€",
        ),
        release_date=ReleaseDate(coming_soon=False, date="11 Feb, 2022"),
        header_image="https://example.com/header.jpg",
        short_description="Short & fun",
    )

    result: MoreData = MoreData.from_app_details(data, "1507530")

    assert result.developers == ["Dev A", "Dev B"]
    assert result.publishers == ["Pub X"]
    assert result.old_price == "4,99€"
    assert result.release_date == "11 Feb, 2022"
    assert result.header_image == "https://example.com/header.jpg"
    assert result.short_description == "Short & fun"


def test_from_app_details_missing_optional_fields_returns_defaults() -> None:
    data = AppDetailsData()  # All optional fields omitted (None)

    result: MoreData = MoreData.from_app_details(data, "123")

    assert result.developers == [], f"Expected empty developers but got {result.developers}"
    assert result.publishers == [], f"Expected empty publishers but got {result.publishers}"
    assert not result.old_price, f"Expected no old_price but got {result.old_price}"
    assert not result.release_date, f"Expected no release_date but got {result.release_date}"
    assert result.header_image is None, f"Expected no header_image but got {result.header_image}"
    assert not result.short_description, f"Expected no short_description but got {result.short_description}"


def test_from_app_details_partial_fields_only_set_present_values() -> None:
    # publishers, price_overview, release_date, header_image, short_description remain None
    data = AppDetailsData(developers=["Solo Dev"])

    result: MoreData = MoreData.from_app_details(data, "999")

    assert result.developers == ["Solo Dev"]
    assert result.publishers == [], f"Expected empty publishers but got {result.publishers}"  # default remains
    assert not result.old_price, f"Expected no old_price but got {result.old_price}"  # not set without price_overview
    assert not result.release_date, f"Expected no release_date but got {result.release_date}"  # not set without release_date
    assert result.header_image is None, f"Expected no header_image but got {result.header_image}"
    assert not result.short_description, f"Expected no short_description but got {result.short_description}"
