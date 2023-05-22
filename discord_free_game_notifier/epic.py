import calendar
import time
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from discord_webhook import DiscordEmbed
from loguru import logger
from pytz import timezone
from requests.utils import requote_uri

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook

# Epic's backend API URL for the free games promotion
EPIC_API: str = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

# HTTP params for the US free games
PARAMS: dict[str, str] = {
    "locale": "en-US",
    "country": "US",
    "allowCountries": "US",
}


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
                start_date: int = calendar.timegm(time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ"))

    # Convert to int to remove the microseconds
    start_date = int(start_date)
    logger.debug(f"\tStarted: {start_date}")

    return start_date


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
                end_date: float = time.mktime(time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ"))

    # Convert to int to remove the microseconds
    end_date = int(end_date)
    logger.debug(f"\tEnds in: {end_date}")

    return end_date


def game_image(game: dict) -> str:
    """Get an image URL for the game.

    Args:
        game: The free game to get the image of.

    Returns:
        str: Returns the image URL of the game.
    """
    # Get the game's image. Image is 2560x1440
    # TODO: Get other image if Thumbnail is not available?
    image_url: str = ""
    for image in game["keyImages"]:
        if image["type"] in ["DieselStoreFrontWide", "Thumbnail"]:
            image_url = image["url"]
    logger.debug(f"\tImage URL: {requote_uri(image_url)}")

    # Epic's image URL has spaces in them, so requote the URL.
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
        logger.debug("\tProduct slug is empty")
        for offer in game["offerMappings"]:
            if offer["pageSlug"]:
                page_slug: str = offer["pageSlug"]
                url = f"https://www.epicgames.com/en-US/p/{page_slug}"
                logger.debug("\tFound page slug")

    logger.debug(f"\tURL: {requote_uri(url)}")

    # Epic's image URL has spaces in them, could happen here too so requote the URL.
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
        logger.debug(f"\tNo promotions found for {game_name}, skipping")
        return False
    return True


def get_free_epic_games() -> Generator[DiscordEmbed | None, Any, None]:
    """Uses an API from Epic to parse a list of free games to find this week's free games.

    Yields:
        Generator[DiscordEmbed | None, Any, None]: Returns a DiscordEmbed object for each free game.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "epic.txt"
    logger.debug(f"Previous games file: {previous_games}")

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w") as f:
            f.write("")

    # Connect to the Epic API and get the free games
    response: requests.Response = requests.get(EPIC_API, params=PARAMS, timeout=10)

    # Find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        game_name: str = game["title"]

        original_price: int = game["price"]["totalPrice"]["originalPrice"]
        discount: int = game["price"]["totalPrice"]["discount"]

        final_price: int = original_price - discount

        for image in game["keyImages"]:
            if image["type"] == "VaultOpened":
                if check_promotion is False:
                    continue

                if already_posted(previous_games, game_name):
                    continue

                send_webhook(f"{game_name} - Could be free game? It is in the 'Epic Vault'", game_service="Epic")
                yield create_embed(previous_games, game)

        # If the original_price - discount is 0, then the game is free.
        if final_price == 0 and (original_price != 0 and discount != 0):
            logger.debug(f"Game: {game_name}")

            if check_promotion is False:
                continue

            if already_posted(previous_games, game_name):
                continue

            logger.debug(f"\tPrice: {original_price / 100}$")
            logger.debug(f"\tDiscount: {discount / 100}$")

            yield create_embed(previous_games, game)


def create_embed(previous_games: Path, game: dict) -> DiscordEmbed | None:
    """Create the embed that we will send to Discord.

    Args:
        previous_games: The file with previous games in, we will add to it after we sent the webhook.
        game: The game JSON.

    Returns:
        Embed: The embed with the free game we will send to Discord.
    """
    embed = DiscordEmbed(description=game["description"])

    url = game_url(game)
    game_name: str = game["title"]

    # Jotun had /home appended to the URL, I have no idea if it
    # is safe to remove it, so we are removing it here and
    # sending a message to the user that we modified the URL.
    if url.endswith("/home"):
        url: str = url[:-5]

    embed.set_author(
        name=game_name,
        url=url,
        icon_url=settings.epic_icon,
    )

    curr_dt: datetime = datetime.now(timezone.utc)
    current_time = int(round(curr_dt.timestamp()))

    end_time: int = promotion_end(game)
    if end_time > current_time:
        embed.add_embed_field(
            name="Start",
            value=f"<t:{promotion_start(game)}:R>",
        )
        embed.add_embed_field(
            name="End",
            value=f"<t:{end_time}:R>",
        )

        seller: str = game["seller"]["name"] if game["seller"] else "Unknown"

        embed.set_footer(text=f"{seller}")

        if image_url := game_image(game):
            embed.set_image(url=image_url)

        # Save the game title to the previous games file, so we don't post it again.
        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_name}\n")

        return embed
    return None


if __name__ == "__main__":
    # Remember to delete previous games if you are testing
    # It can be found in %appdata%\TheLovinator\discord_free_game_notifier
    for free_game in get_free_epic_games():
        if free_game:
            webhook_response: requests.Response = send_embed_webhook(free_game)
            if not webhook_response.ok:
                msg: str = (
                    "Error when checking game for Epic:\n"
                    f"{webhook_response.status_code} - {webhook_response.reason}: {webhook_response.text}"
                )
                logger.error(msg)
