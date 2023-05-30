import calendar
import time
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz
import requests
from discord_webhook import DiscordEmbed
from loguru import logger
from requests.adapters import HTTPAdapter, Retry
from requests.utils import requote_uri

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

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
    logger.info(f"\tStarted: {start_date}")

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
    logger.info(f"\tEnds in: {end_date}")

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
            logger.debug(f"\tFound image URL: {image_url} (type: {image['type']})")

    # This fixes https://github.com/TheLovinator1/discord-free-game-notifier/issues/70
    if not image_url:
        for image in game["keyImages"]:
            if image["type"] == "OfferImageWide":
                image_url = image["url"]
                logger.debug(f"\tFound image URL: {image_url} (type: {image['type']})")

    logger.info(f"\tImage URL: {requote_uri(image_url)}")

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

    logger.info(f"\tURL: {requote_uri(url)}")

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
        logger.info(f"\tNo promotions found for {game_name}, skipping")
        return False
    return True


def get_free_epic_games() -> Generator[DiscordEmbed | None, Any, None]:  # noqa: C901, PLR0912
    """Uses an API from Epic to parse a list of free games to find this week's free games.

    Yields:
        Generator[DiscordEmbed | None, Any, None]: Returns a DiscordEmbed object for each free game.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "epic.txt"
    logger.info(f"Previous games file: {previous_games}")

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w") as f:
            f.write("")

    # Use the same session for all requests to Epic
    session = requests.Session()

    # Retry the request if it fails.
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

    # Use the same session for all requests.
    session.mount("http://", HTTPAdapter(max_retries=retries))

    # Connect to the Epic API and get the free games
    response: requests.Response = session.get(EPIC_API, params=PARAMS, timeout=10)

    # Find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        game_name: str = game["title"]
        logger.info(f"Game: {game_name}")

        # This are games that will be free next week, so skip them
        if game_name == "Mystery Game":
            logger.info(f"\tSkipping {game_name}")
            continue

        # What the price was before the discount, in dollar cents
        original_price: int = game["price"]["totalPrice"]["originalPrice"]

        # How much the discount is, this should always be the same as the original price, in dollar cents
        discount: int = game["price"]["totalPrice"]["discount"]

        # What the price is after the discount, if this is 0, then the game will be sent to Discord, in dollar cents
        final_price: int = original_price - discount

        logger.info(f"\tOriginal price: {original_price} ({original_price/1000}$)")
        logger.info(f"\tDiscount: {discount}({discount/1000}$)")
        logger.info(f"\tFinal price: {final_price} ({final_price/1000}$)")

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

        # If the original_price - discount is 0, then the game is free.
        if final_price == 0 and (original_price != 0 and discount != 0):
            if check_promotion is False:
                continue

            if already_posted(previous_games, game_name):
                continue

            yield create_embed(previous_games, game)


def create_embed(previous_games: Path, game: dict) -> DiscordEmbed | None:
    """Create the embed that we will send to Discord.

    Args:
        previous_games: The file with previous games in, we will add to it after we sent the webhook.
        game: The game JSON.

    Returns:
        Embed: The embed with the free game we will send to Discord.
    """
    # Create the embed that we will send to Discord.
    # Description is the game's description.
    embed = DiscordEmbed(description=game["description"])

    # The URL to the store page.
    url = game_url(game)

    # The name of the game.
    game_name: str = game["title"]

    # Jotun had /home appended to the URL and that broke the link, so I guess remove it for all the future games?
    # Broken: https://www.epicgames.com/en-US/p/jotun/home
    # Fixed: https://www.epicgames.com/en-US/p/jotun
    if url.endswith("/home"):
        url: str = url[:-5]

    # Show the game name, Epic icon and the URL to the game.
    embed.set_author(
        name=game_name,
        url=url,
        icon_url=settings.epic_icon,
    )

    # Get the current time so we can check that the game is still free.
    curr_dt: datetime = datetime.now(tz=pytz.UTC)
    current_time = int(round(curr_dt.timestamp()))

    # When the game stops being free.
    end_time: int = promotion_end(game)

    # Only send the embed if the game is still free.
    if end_time > current_time:
        # When the game started being free
        embed.add_embed_field(
            name="Start",
            value=f"<t:{promotion_start(game)}:R>",
        )

        # When the games stops being free
        embed.add_embed_field(
            name="End",
            value=f"<t:{end_time}:R>",
        )

        # Get the seller name
        seller: str = game["seller"]["name"] if game["seller"] else "Unknown"

        # Some games are sold by Epic Dev Test Account, we don't want to show that.
        if seller not in ["Epic Dev Test Account", "Unknown"]:
            embed.set_footer(text=f"{seller}")

        # Get the image URL and add it to the embed
        if image_url := game_image(game):
            embed.set_image(url=image_url)

        # Save the game title to the previous games file, so we don't post it again.
        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_name}\n")

        # Return the embed so we can send it to Discord
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
