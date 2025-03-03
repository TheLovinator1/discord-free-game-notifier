from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from discord_webhook import DiscordEmbed
from loguru import logger
from selectolax.parser import HTMLParser, Node

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

if TYPE_CHECKING:
    from collections.abc import Generator

STEAM_URL: str = "https://store.steampowered.com/search/?maxprice=free&specials=1"
DEFAULT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"


@dataclass(slots=True)
class MoreData:
    """A dataclass to hold more data about the game."""

    # "Stellar Mess is a 2D point&amp;click adventure game, set somewhere in Argentinean Patagonia. The game is inspired by early classic EGA games of the genre." # noqa: E501
    short_description: str = ""

    # "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1507530/header.jpg?t=1737679003"
    header_image: str = "https://cdn.cloudflare.steamstatic.com/steam/apps/753/header.jpg"

    # ["Tibba Games"]
    developers: list[str] = field(default_factory=list)

    # ["Tibba Games"]
    publishers: list[str] = field(default_factory=list)

    # "4,99€"
    old_price: str = ""

    # "11 Feb, 2022"
    release_date: str = ""

    reviews: str = ""


def get_more_data(game_id: str) -> MoreData:  # noqa: C901, PLR0912
    """Get more data about the game.

    Args:
        game_id (str): The game ID.

    Returns:
        MoreData: A dataclass with more data about the game or empty data.
    """
    # 753 is the default game ID
    if game_id == "753":
        return MoreData()

    logger.debug(f"Getting more data for {game_id=}")
    appdetails_response: requests.Response = requests.get(
        url=f"https://store.steampowered.com/api/appdetails?appids={game_id}",
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=30,
    )

    more_data = MoreData()
    if appdetails_response.ok:
        game_data_from_api: dict = appdetails_response.json()
        if game_data_from_api and game_data_from_api.get(game_id, {}).get("success", False):
            logger.debug(f"{game_data_from_api=}")

            game_data: dict = game_data_from_api.get(game_id, {}).get("data", {})
            if game_data:
                header_image: str | None = game_data.get("header_image")
                if header_image:
                    logger.debug(f"{header_image=} for {game_id=}")
                    more_data.header_image = header_image

                short_description: str | None = game_data.get("short_description")
                if short_description:
                    logger.debug(f"{short_description=} for {game_id=}")
                    more_data.short_description = short_description

                developers: list[str] | None = game_data.get("developers")
                if developers:
                    logger.debug(f"{developers=} for {game_id=}")
                    more_data.developers = developers

                publishers: list[str] | None = game_data.get("publishers")
                if publishers:
                    logger.debug(f"{publishers=} for {game_id=}")
                    more_data.publishers = publishers

                price_overview: dict | None = game_data.get("price_overview")
                if price_overview:
                    more_data.old_price = price_overview.get("initial_formatted", "")

                release_date: dict | None = game_data.get("release_date")
                if release_date:
                    more_data.release_date = release_date.get("date", "")

    logger.debug(f"Getting reviews for {game_id=}")

    # {"success":1,"query_summary":{"num_reviews":0,"review_score":5,"review_score_desc":"Mixed","total_positive":125,"total_negative":74,"total_reviews":199},"reviews":[],"cursor":"*"} # noqa: E501
    reviews_response: requests.Response = requests.get(
        url=f"https://store.steampowered.com/appreviews/{game_id}?json=1&language=all&num_per_page=0&purchase_type=all",
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=30,
    )

    if reviews_response.ok:
        game_data: dict = reviews_response.json()
        if game_data and game_data.get("success", False):
            logger.debug(f"{game_data=}")
            reviews: str | None = game_data.get("query_summary", {}).get("review_score_desc")
            if reviews:
                logger.debug(f"{reviews=} for {game_id=}")
                more_data.reviews = reviews

    return more_data


def get_free_steam_games() -> Generator[DiscordEmbed, Any, None]:
    """Go to the Steam store and check for free games and return them.

    Yields:
        Generator[DiscordEmbed, Any, None]: A generator with Discord
    """
    request: requests.Response = requests.get(url=STEAM_URL, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=30)
    parser = HTMLParser(request.text)
    games: list[Node] = parser.css("a.search_result_row")

    for game in games:
        title_element = game.css_first("span.title")
        if title_element is None:
            logger.warning("Could not find title for game, skipping")
            continue

        game_name: str = title_element.text(strip=True)

        logger.info(f"Checking game: {game_name}")
        previous_games_file: Path = Path(settings.app_dir) / "steam.txt"
        if already_posted(previous_games_file, game_name):
            logger.info(f"Game already posted: {game_name}")
            continue

        game_url: str = game.attributes.get("href") or STEAM_URL
        game_id: str = game.attributes.get("data-ds-appid") or "753"  # Default to Steam app ID

        more_data: MoreData = get_more_data(game_id)

        embed = DiscordEmbed(color="fcc603")
        embed.set_author(name="Steam", url=game_url, icon_url=settings.steam_icon)

        if more_data.header_image:
            embed.set_image(url=more_data.header_image)

        if more_data.short_description:
            embed.description = html.unescape(more_data.short_description)

        if more_data.old_price:
            embed.add_embed_field(name="Old Price", value=more_data.old_price)

        if more_data.release_date:
            embed.add_embed_field(name="Release Date", value=more_data.release_date)

        if more_data.reviews:
            embed.add_embed_field(name="Reviews", value=more_data.reviews)

        set_game_footer(more_data, embed)

        logger.debug(f"More data for {game_name}: {more_data}")
        logger.info(f"Posting game: {game_name}")

        with Path.open(Path(settings.app_dir) / "steam.txt", "a+", encoding="utf-8") as file:
            file.write(f"{game_name}\n")

        yield embed
    return


def set_game_footer(more_data: MoreData, embed: DiscordEmbed) -> None:
    """Set the game developer/publisher information in the embed footer.

    Args:
        more_data (MoreData): The dataclass with more data about the game.
        embed (DiscordEmbed): The Discord embed object.
    """
    if not (more_data.developers or more_data.publishers):
        return

    if more_data.developers == more_data.publishers:
        footer: str = f"Developed by {', '.join(more_data.developers)}"
    else:
        developers: str = f"{', '.join(more_data.developers)}" if more_data.developers else ""
        publishers: str = f"{', '.join(more_data.publishers)}" if more_data.publishers else ""

        if developers and publishers:
            footer = f"Developed by {developers} | Published by {publishers}"
        else:
            footer = f"Developed by {developers or publishers}"

    embed.set_footer(text=footer)


if __name__ == "__main__":
    for free_game in get_free_steam_games():
        if free_game:
            response: requests.Response = send_embed_webhook(free_game)
            if not response.ok:
                logger.error(f"Error when checking game for Steam:\n{response.status_code} - {response.reason}: {response.text}")
