from __future__ import annotations

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

    Yields:
        DiscordEmbed: Embed for the free GOG games.
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
        if not already_posted(previous_games, game_name):
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

            yield create_embed(
                previous_games=previous_games,
                game_name=game_name,
                game_url=game_url,
                image_url=image_url,
                no_claim=True,
            )


def get_giveaway_link(giveaway: Tag | NavigableString | None, game_name: str) -> str:
    """Get the giveaway link from the GOG giveaway.

    Args:
        giveaway: The giveaway tag.
        game_name: The game name.

    Returns:
        The giveaway link. Defaults to https://www.gog.com/ if not found.
    """
    gog_giveaway_link: Tag | NavigableString | None | int = giveaway.find("a", {"selenium-id": "giveawayOverlayLink"})  # type: ignore  # noqa: PGH003
    if not hasattr(gog_giveaway_link, "attrs"):
        logger.bind(game_name=game_name).error("No giveaway link found on GOG for {} because it's doesn't have 'attrs'", giveaway)
        return "https://www.gog.com/"

    # Only allow Tag
    if not isinstance(gog_giveaway_link, Tag):
        logger.bind(game_name=game_name).error("No giveaway link found on GOG for {} because it's not a 'Tag'", giveaway)
        return "https://www.gog.com/"

    giveaway_link: str = gog_giveaway_link.attrs["href"]
    logger.bind(game_name=game_name).info(f"Giveaway link: {giveaway_link}")
    return giveaway_link


def get_game_image(giveaway: BeautifulSoup, game_name: str) -> str:
    """Get the game image from the GOG giveaway.

    Args:
        giveaway: The giveaway tag.
        game_name: The game name.

    Returns:
    The game image URL. Defaults to a placeholder image if not found.
    """
    default_image = "https://images.gog.com/86843ada19050958a1aecf7de9c7403876f74d53230a5a96d7e615c1348ba6a9.webp"

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
        return default_image

    # Check if image_url_class has attrs
    if not hasattr(image_url_class, "attrs"):
        logger.bind(game_name=game_name).error("No attrs found on GOG for {}", giveaway)
        return default_image

    images: list[str] = image_url_class.attrs["srcset"].strip().split()  # type: ignore  # noqa: PGH003
    image_url = images[0]

    if not image_url:
        logger.bind(game_name=game_name).error("No image URL found on GOG for {}", giveaway)
        return default_image

    logger.bind(game_name=game_name).info(f"Image URL: {image_url}")

    return image_url


def get_game_name(giveaway_soup: BeautifulSoup, giveaway: Tag | NavigableString | None) -> str:
    """Get the game name from the GOG giveaway.

    Args:
        giveaway_soup: The giveaway tag.
        giveaway: The giveaway tag.

    Returns:
        The game name. Defaults to "GOG Giveaway" if not found.
    """
    img_tag: Tag | NavigableString | None = giveaway_soup.find("img", alt=True)
    if not hasattr(img_tag, "attrs"):
        logger.bind(game_name="GOG").error("No img tag found on GOG for {}", giveaway)
        return "GOG Giveaway"

    # Extract the game name from the alt attribute
    if img_tag and isinstance(img_tag, Tag):
        game_name_alt: str | list[str] = img_tag["alt"]
        if isinstance(game_name_alt, str) and game_name_alt:
            game_name: str = game_name_alt.replace(" giveaway", "") if img_tag else "Game name not found"
        if isinstance(game_name_alt, list) and game_name_alt:
            game_name = game_name_alt[0].replace(" giveaway", "") if img_tag else "Game name not found"
            logger.bind(game_name=game_name).warning("was a list of strings so could be wrong?")
    else:
        game_name = "GOG Giveaway"
        logger.bind(game_name=game_name).error("No img tag found on GOG for {}", img_tag)

    return game_name


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
    giveaway: Tag | NavigableString | None = soup.find("giveaway")
    giveaway_soup: BeautifulSoup = BeautifulSoup(str(giveaway), "html.parser")

    if giveaway is None:
        return None

    # Get the game name
    game_name: str = get_game_name(giveaway_soup=giveaway_soup, giveaway=giveaway)

    if already_posted(previous_games=previous_games, game_name=game_name):
        return None

    giveaway_link: str = get_giveaway_link(giveaway=giveaway, game_name=game_name)
    image_url: str = get_game_image(giveaway=giveaway_soup, game_name=game_name)

    # Create the embed and add it to the list of free games.
    return create_embed(
        previous_games=previous_games,
        game_name=game_name,
        game_url=giveaway_link,
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
