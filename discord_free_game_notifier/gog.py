from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from discord_webhook import DiscordEmbed
from loguru import logger

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

if TYPE_CHECKING:
    from collections.abc import Generator


def get_game_name(banner_title_text: str) -> str:
    """Get the game name from the banner title.

    Args:
        banner_title_text: The banner title. We will run a regex to get the game name.

    Returns:
        str: The game name, GOG Giveaway if not found.
    """
    if result := re.search(
        r"being with us! Claim (.*?) as a token of our gratitude!",
        banner_title_text,
    ):
        return result[1]
    return "GOG Giveaway"


def create_embed(
    previous_games: Path,
    game_name: str = "",
    image_url: str = "",
    game_url: str = "",
    *,
    no_claim: bool = False,
) -> DiscordEmbed:
    """Create the embed that we will send to Discord.

    Args:
        previous_games: The file where we store old games in.
        game_name: The game name.
        game_url: URL to the game.
        image_url: Game image.
        no_claim: Don't use https://www.gog.com/giveaway/claim

    Returns:
        Embed: The embed we will send to Discord.
    """
    if not game_name:
        game_name = "GOG Giveaway"

    if not game_url:
        game_url = "https://www.gog.com/"

    description: str = (
        f"[Click here to claim {game_name}!](https://www.gog.com/giveaway/claim)\n"
        "[Click here to unsubscribe from emails!]("
        "https://www.gog.com/en/account/settings/subscriptions)"
    )

    if no_claim:
        description = (
            f"[Click here to claim {game_name}!]({game_url})\n"
            "[Click here to unsubscribe from emails!]("
            "https://www.gog.com/en/account/settings/subscriptions)"
        )

    embed = DiscordEmbed(description=description)
    embed.set_author(name=game_name, url=game_url, icon_url=settings.gog_icon)
    if image_url:
        image_url = image_url.removesuffix(",")

        if image_url.startswith("//"):
            image_url = f"https:{image_url}"

        embed.set_image(url=image_url)

    with Path.open(previous_games, "a+", encoding="utf-8") as file:
        file.write(f"{game_name}\n")

    return embed


def get_free_gog_game_from_store() -> Generator[DiscordEmbed | None, Any, None]:
    """Check if free GOG game from games store.

    Returns:
        Generator[Embed, Any, None]: Embed for the free GOG games.
    """
    previous_games: Path = Path(settings.app_dir) / "gog.txt"

    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")
    request: requests.Response = requests.get(
        "https://www.gog.com/en/games?priceRange=0,0&discounted=true",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        },
        timeout=30,
    )
    soup = BeautifulSoup(request.text, "html.parser")

    games: Tag | NavigableString | None = soup.find(
        "div",
        {"selenium-id": "paginatedProductsGrid"},
    )

    if games is None:
        logger.bind(game_name="GOG").debug("No free games found")
        return

    if not hasattr(games, "children"):
        logger.bind(game_name="GOG").debug("No free games found")
        return

    # Print children
    for child in games.children:  # type: ignore  # noqa: PGH003
        if not hasattr(child, "attrs"):
            continue

        # Game name
        game_class = child.find("div", {"selenium-id": "productTileGameTitle"})  # type: ignore  # noqa: PGH003
        game_name = game_class["title"]  # type: ignore  # noqa: PGH003
        logger.bind(game_name=game_name).info(f"Game name: {game_name}")

        # Game URL
        game_url = child.find("a", {"class": "product-tile--grid"})["href"]  # type: ignore  # noqa: PGH003
        logger.bind(game_name=game_name).info(f"Game URL: {game_url}")

        # Game image
        image_url_class: Tag | NavigableString | None = child.find(  # type: ignore  # noqa: PGH003
            "source",
            attrs={"srcset": True},
        )
        if hasattr(image_url_class, "attrs"):
            images: list[str] = image_url_class.attrs["srcset"].strip().split()  # type: ignore  # noqa: PGH003
            image_url: str = f"{images[0]}"
            logger.bind(game_name=game_name).info(f"Image URL: {image_url}")
        else:
            image_url = ""

        if already_posted(previous_games, game_name):
            yield None

        # Create the embed and add it to the list of free games.
        yield create_embed(
            previous_games=previous_games,
            game_name=game_name,
            game_url=game_url,
            image_url=image_url,
            no_claim=True,
        )


def get_free_gog_game() -> DiscordEmbed | None:
    """Check if free GOG game.

    Returns:
        DiscordEmbed: Embed for the free GOG games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "gog.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    request: requests.Response = requests.get(
        "https://www.gog.com/",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        },
        timeout=30,
    )

    soup = BeautifulSoup(request.text, "html.parser")
    giveaway: Tag | NavigableString | None = soup.find("a", {"id": "giveaway"})

    if giveaway is None:
        return None

    # Game name
    banner_title: Tag | NavigableString | None = giveaway.find(
        "span",
        class_="giveaway-banner__title",  # type: ignore  # noqa: PGH003
    )

    # If no banner title, return an empty list
    if banner_title is None:
        logger.error("No banner title found on GOG for {}", giveaway)
        return None

    # Check if the game has already been posted
    game_name: str = get_game_name(banner_title.text)
    logger.bind(game_name=game_name).info(f"Game name: {game_name}")

    # Game URL
    ng_href: str = giveaway.attrs["ng-href"]  # type: ignore  # noqa: PGH003
    game_url: str = f"https://www.gog.com{ng_href}"
    logger.bind(game_name=game_name).info(f"URL: {game_url}")

    # Game image
    image_url_class: Tag | NavigableString | None = giveaway.find(
        "source",
        attrs={"srcset": True},  # type: ignore  # noqa: PGH003
    )

    # If no image URL, return an empty list
    if image_url_class is None:
        logger.bind(game_name=game_name).error(
            "No image URL found on GOG for {}",
            giveaway,
        )
        return None

    # Check if image_url_class has attrs
    if not hasattr(image_url_class, "attrs"):
        logger.bind(game_name=game_name).error("No attrs found on GOG for {}", giveaway)
        return None

    images: list[str] = image_url_class.attrs["srcset"].strip().split()  # type: ignore  # noqa: PGH003
    image_url = images[0]
    logger.bind(game_name=game_name).info(f"Image URL: {image_url}")

    if already_posted(previous_games, game_name):
        return None

    # Create the embed and add it to the list of free games.
    return create_embed(
        previous_games=previous_games,
        game_name=game_name,
        game_url=game_url,
        image_url=image_url,
    )


if __name__ == "__main__":
    if gog_embed := get_free_gog_game():
        response: requests.Response = send_embed_webhook(gog_embed)
        if not response.ok:
            logger.error(
                "Error when checking game for GOG:\n{} - {}: {}",
                response.status_code,
                response.reason,
                response.text,
            )

    for game in get_free_gog_game_from_store():
        if game is None:
            continue

        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                "Error when checking game for GOG:\n{} - {}: {}",
                response.status_code,
                response.reason,
                response.text,
            )
