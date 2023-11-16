from __future__ import annotations

import calendar
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytz
import requests
from discord_webhook import DiscordEmbed
from loguru import logger
from requests.adapters import HTTPAdapter, Retry
from requests.utils import requote_uri

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

if TYPE_CHECKING:
    from collections.abc import Generator


def promotion_start(game: dict) -> int:
    """Get the start date of a game's promotion.

    offer["startDate"] = "2022-04-07T15:00:00.000Z"

    Args:
        game: The game JSON.

    Returns:
        int: Returns the start date of the game's promotion.
    """
    start_date = 0
    if game["promotions"]:
        for promotion in game["promotions"]["promotionalOffers"]:
            for offer in promotion["promotionalOffers"]:
                if not offer["startDate"] or offer["startDate"] == "":
                    logger.bind(game_name=game["title"]).error("Start date is empty")
                    return 0

                start_date: int = calendar.timegm(
                    time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                )
    logger.bind(game_name=game["title"]).info(f"Starts in: {int(start_date)}")
    return int(start_date)


def promotion_end(game: dict) -> int:
    """Get the end date of a game's promotion.

    offer["endDate"] = "2022-04-07T15:00:00.000Z"

    Args:
        game: The game JSON.

    Returns:
        int: Returns the end date of the game's promotion.
    """
    end_date = 0
    if game["promotions"]:
        for promotion in game["promotions"]["promotionalOffers"]:
            for offer in promotion["promotionalOffers"]:
                if not offer["endDate"] or offer["endDate"] == "":
                    logger.bind(game_name=game["title"]).error("End date is empty")
                    return 0

                end_date: float = time.mktime(
                    time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                )

    logger.bind(game_name=game["title"]).info(f"Ends in: {int(end_date)}")
    return int(end_date)


def game_image(game: dict) -> str:
    """Get an image URL for the game.

    Args:
        game: The free game to get the image of.

    Returns:
        str: Returns the image URL of the game.
    """
    image_url: str = ""
    for image in game["keyImages"]:
        if image["type"] in ["DieselStoreFrontWide", "Thumbnail"]:
            image_url = image["url"]
            logger.bind(game_name=game["title"]).debug(
                f"Found image URL: {image_url} (type: {image['type']})",
            )

    # This fixes https://github.com/TheLovinator1/discord-free-game-notifier/issues/70
    if not image_url:
        for image in game["keyImages"]:
            if image["type"] == "OfferImageWide":
                image_url = image["url"]
                logger.bind(game_name=game["title"]).debug(
                    f"Found image URL: {image_url} (type: {image['type']})",
                )

    logger.bind(game_name=game["title"]).info(f"Image URL: {requote_uri(image_url)}")
    return requote_uri(image_url)


def game_url(game: dict) -> str:
    """If you click the game name, you'll be taken to the game's page on Epic.

    Args:
        game: The game JSON

    Returns:
        str: Returns the URL of the game.
    """
    url = "https://store.epicgames.com/"
    if product_slug := game["productSlug"]:
        url: str = f"https://www.epicgames.com/en-US/p/{product_slug}"
    else:
        logger.bind(game_name=game["title"]).debug("Product slug is empty")
        for offer in game["offerMappings"]:
            if offer["pageSlug"]:
                page_slug: str = offer["pageSlug"]
                url = f"https://www.epicgames.com/en-US/p/{page_slug}"
                logger.bind(game_name=game["title"]).debug("Found page slug")

    logger.bind(game_name=game["title"]).info(f"URL: {requote_uri(url)}")
    return requote_uri(url)


def check_promotion(game: dict) -> bool:
    """Check if the game has a promotion, only free games has these.

    Args:
        game: The game JSON

    Returns:
        bool: True if game has promotion
    """
    if not game["promotions"]:
        game_name: str = game["title"]
        logger.bind(game_name=game["title"]).info(
            f"No promotions found for {game_name}, skipping",
        )
        return False
    return True


def get_response() -> requests.Response:
    """Get the response from Epic.

    Returns:
        Response: The response from Epic.
    """
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            ),
        ),
    )
    response: requests.Response = session.get(
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
        timeout=10,
    )
    logger.debug(f"Response: {response.status_code} - {response.reason}")
    return response


def if_mystery_game(game: dict) -> bool:
    """Check if the game is a mystery game.

    Mystery games are not free games, but games that are coming soon.

    Args:
        game: The game JSON

    Returns:
        bool: True if game is a mystery game
    """
    if game.get("title", "") == "Mystery Game":
        logger.bind(game_name=game["title"]).info("Mystery game, skipping")
        return True
    return False


def get_free_epic_games() -> Generator[DiscordEmbed | None, Any, None]:  # noqa: C901, PLR0912
    """Get the free games from Epic.

    Yields:
        Embed: The embed with the free game we will send to Discord.
    """
    previous_games: Path = Path(settings.app_dir) / "epic.txt"
    if not Path.exists(previous_games):
        logger.bind(game_name="Epic").info("Creating file for previous games")
        with Path.open(previous_games, "w") as f:
            f.write("")

    response: requests.Response = get_response()
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        game_name: str = game["title"]
        logger.bind(game_name=game["title"]).info(f"Checking {game_name}")

        if if_mystery_game(game):
            continue

        original_price: int = game["price"]["totalPrice"]["originalPrice"]
        discount: int = game["price"]["totalPrice"]["discount"]
        final_price: int = original_price - discount

        logger.bind(game_name=game["title"]).info(f"Original price: {original_price}")
        logger.bind(game_name=game["title"]).info(f"Discount: {discount}")
        logger.bind(game_name=game["title"]).info(f"Final price: {final_price}")

        for image in game["keyImages"]:
            if image["type"] == "VaultOpened":
                if check_promotion is False:
                    continue

                if already_posted(previous_games, game_name):
                    continue

                yield create_embed(previous_games, game)

            # This fixes https://github.com/TheLovinator1/discord-free-game-notifier/issues/70
            for cat in game["categories"]:
                if cat["path"] == "freegames/vaulted" and game["status"] == "ACTIVE":
                    if check_promotion is False:
                        continue

                    if already_posted(previous_games, game_name):
                        continue

                    yield create_embed(previous_games, game)

        if final_price == 0 and (original_price != 0 and discount != 0):
            logger.bind(game_name=game["title"]).info("Game is free")
            if check_promotion is False:
                continue

            if already_posted(previous_games, game_name):
                continue

            yield create_embed(previous_games, game)


def create_embed(previous_games: Path, game: dict) -> DiscordEmbed | None:
    """Create the embed for the game.

    Args:
        previous_games: The file where we store old games in.
        game: The game JSON

    Returns:
        Embed: The embed with the free game we will send to Discord.
    """
    description: str = game["description"] or "No description found"
    logger.bind(game_name=game["title"]).info(f"Description: {description}")
    embed = DiscordEmbed(description=description)
    url = game_url(game)
    game_name: str = game["title"]

    # Jotun had /home appended to the URL and that broke the link
    # Broken: https://www.epicgames.com/en-US/p/jotun/home
    # Fixed: https://www.epicgames.com/en-US/p/jotun
    if url.endswith("/home"):
        logger.bind(game_name=game["title"]).debug("URL ends with /home")
        url: str = url[:-5]

    embed.set_author(name=game_name, url=url, icon_url=settings.epic_icon)

    curr_dt: datetime = datetime.now(tz=pytz.UTC)
    current_time = int(round(curr_dt.timestamp()))
    end_time: int = promotion_end(game)
    start_time: int = promotion_start(game)

    if end_time > current_time or (end_time == 0 and start_time != 0):
        if start_time != 0:
            embed.add_embed_field(name="Start", value=f"<t:{start_time}:R>")
        if end_time != 0:
            embed.add_embed_field(name="End", value=f"<t:{end_time}:R>")

        seller: str = game["seller"]["name"] if game["seller"] else "Unknown"

        if seller not in ["Epic Dev Test Account", "Unknown"]:
            logger.bind(game_name=game["title"]).info(f"Seller: {seller}")
            embed.set_footer(text=f"{seller}")

        if image_url := game_image(game):
            logger.bind(game_name=game["title"]).info(f"Image: {image_url}")
            embed.set_image(url=image_url)

        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            logger.bind(game_name=game["title"]).info("Saving game to file")
            file.write(f"{game_name}\n")

        return embed

    logger.bind(game_name=game["title"]).info(
        f"Game has ended, skipping. End time: {end_time}. Current time: {current_time}",
    )
    return None


if __name__ == "__main__":
    for free_game in get_free_epic_games():
        if free_game:
            webhook_response: requests.Response = send_embed_webhook(free_game)
            if not webhook_response.ok:
                msg: str = (
                    "Error when checking game for Epic:\n"
                    f"{webhook_response.status_code} - {webhook_response.reason}: {webhook_response.text}"  # noqa: E501
                )
                logger.error(msg)
