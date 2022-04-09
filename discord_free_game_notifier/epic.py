"""Modified version of https://github.com/andrewguest/slack-free-epic-games"""

import calendar
import os
import time
from pathlib import Path
from typing import Dict, List

import requests
from dhooks import Embed

from discord_free_game_notifier import settings

# Epic's backend API URL for the free games promotion
EPIC_API: str = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"  # noqa: E501, pylint: disable=line-too-long

# HTTP params for the US free games
PARAMS: Dict[str, str] = {
    "locale": "en-US",
    "country": "US",
    "allowCountries": "US",
}


def game_original_price(game):
    """Get the original price of a game. This is in cents. Currency is
    Dollar.

    Args:
        game (_type_): The free game to get the original price of.

    Returns:
        _type_: Returns the price in cents of the game before discount.
    """
    # TODO: Add support for different currencies
    price = game["price"]["totalPrice"]["originalPrice"]
    settings.logger.debug(f"\tPrice: {price/100}$")

    return price


def game_discount(game):
    """Get the discount of a game. This is in cents. Currency is Dollar.

    Args:
        game (_type_): The free game to get the discount of.

    Returns:
        _type_: Returns the discount in cents.
    """
    # TODO: Add support for different currencies
    discount = game["price"]["totalPrice"]["discount"]
    settings.logger.debug(f"\tDiscount: {discount/100}$")

    return discount


def game_final_price(original_price, discount):
    """Calculate the final price of a game.

    Args:
        original_price (_type_): The price before discount.
        discount (_type_): The discount.

    Returns:
        _type_: Returns the final price of the game after discount.
    """
    return original_price - discount


def promotion_start(game):
    """Get the start date of a game's promotion.

    offer["startDate"] = "2022-04-07T15:00:00.000Z"

    Args:
        game (_type_): The free game to get the start date of.

    Returns:
        _type_: Returns the start date of the game's promotion.
    """
    start_date = 0

    if game["promotions"]:
        for promotion in game["promotions"]["promotionalOffers"]:
            for offer in promotion["promotionalOffers"]:

                start_date = calendar.timegm(
                    time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
                )

    # Convert to int to remove the microseconds
    start_date = int(start_date)
    settings.logger.debug(f"\tStarted: {start_date}")

    return start_date


def promotion_end(game):
    """Get the end date of a game's promotion.

    offer["endDate"] = "2022-04-07T15:00:00.000Z"

    Args:
        game (_type_): The free game to get the end date of.

    Returns:
        _type_: Returns the end date of the game's promotion.
    """
    end_date = 0

    if game["promotions"]:
        for promotion in game["promotions"]["promotionalOffers"]:
            for offer in promotion["promotionalOffers"]:
                end_date = time.mktime(
                    time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
                )

    # Convert to int to remove the microseconds
    end_date = int(end_date)
    settings.logger.debug(f"\tEnds in: {end_date}")

    return end_date


def game_publisher(game):
    """Get the publisher of a game.

    Args:
        game (_type_): The free game to get the publisher of.

    Returns:
        _type_: Returns the publisher of the game.
    """
    publisher = ""

    for attribute in game["customAttributes"]:
        if attribute["key"] == "publisherName":
            publisher = attribute["value"]

    if publisher is None:
        publisher = "Unknown"

    settings.logger.debug(f"\tPublisher: {publisher}")

    return publisher


def game_developer(game):
    """Get the developer of a game.

    Args:
        game (_type_): The free game to get the developer of.

    Returns:
        _type_: Returns the developer of the game.
    """
    developer = ""

    for attribute in game["customAttributes"]:
        if attribute["key"] == "developerName":
            developer = attribute["value"]

    if developer is None:
        developer = "Unknown"

    settings.logger.debug(f"\tDeveloper: {developer}")

    return developer


def game_image(game):
    """Get a image URL for the game.

    Args:
        game (_type_): The free game to get the image of.

    Returns:
        _type_: Returns the image URL of the game.
    """
    # Get the game's image. Image is 2560x1440
    image_url = ""
    for image in game["keyImages"]:
        if image["type"] in ["DieselStoreFrontWide", "Thumbnail"]:
            image_url = image["url"]
    settings.logger.debug(f"\tImage URL: {image_url}")

    return image_url


def game_url(game) -> str:
    """If you click the game name, you'll be taken to the game's page on Epic

    Args:
        game (_type_): The free game to get the URL of.

    Returns:
        str: Returns the URL of the game.
    """
    url = f"https://www.epicgames.com/store/en-US/p/{game['urlSlug']}"
    settings.logger.debug(f"\tURL: {url}")

    return url


def get_free_epic_games() -> List[Embed]:
    """Uses an API from Epic to parse a list of free games to find this
    week's free games.

    Original source:
    https://github.com/andrewguest/slack-free-epic-games/blob/main/lambda_function.py#L18

    Returns:
        List[Embed]: List of Embeds that will be sent to Discord.
    """
    free_games: List[Embed] = []

    # Save previous free games to a file so we don't post the same games again
    previous_games: Path = Path(settings.app_dir) / "epic.txt"
    settings.logger.debug(f"Previous games file: {previous_games}")

    # Create file if it doesn't exist
    if not os.path.exists(previous_games):
        open(previous_games, "w", encoding="utf-8").close()

    # Connect to the Epic API and get the free games
    response = requests.get(EPIC_API, params=PARAMS)

    # Find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        game_name = game["title"]
        original_price = game_original_price(game)
        discount = game_discount(game)
        final_price = game_final_price(original_price, discount)

        # If the original_price - discount is 0, then the game is free
        if (final_price) == 0 and (original_price != 0 and discount != 0):
            settings.logger.debug(f"Game: {game_name}")

            if not game["promotions"]:
                settings.logger.debug(
                    f"\tNo promotions found for {game_name}, skipping"
                )
                continue

            # Check if the game has already been posted
            if os.path.isfile(previous_games):
                with open(previous_games, "r", encoding="utf-8") as file:
                    if game_name in file.read():
                        settings.logger.debug(
                            "\tHas already been posted before. Skipping!"
                        )
                        continue

            image_url = game_image(game)

            embed = Embed(
                description=game["description"],
                color=0xFFFFFF,
                timestamp="now",
            )
            embed.set_author(
                name=game_name,
                url=game_url(game),
                icon_url="https://lovinator.space/Epic_Games_logo.png",
            )

            # Discord has dynamic timestamps. 1641142179 is the Unix timestamp
            # <t:1641142179:d> = 02/01/2022
            # <t:1641142179:f> = 2 January 2022 17:49
            # <t:1641142179:t> = 17:49
            # <t:1641142179:D> = 2 January 2022
            # <t:1641142179:F> = Sunday, 2 January 2022 17:49
            # <t:1641142179:R> = 2 minutes ago
            # <t:1641142179:T> = 17:49:39
            embed.add_field(
                name="Start",
                value=f"<t:{promotion_start(game)}:R>",
            )
            embed.add_field(
                name="End",
                value=f"<t:{promotion_end(game)}:R>",
            )

            # Only add developer if it's not the same as the publisher
            # Otherwise, it'll will look like "Square Enix | Square Enix"
            if game_publisher(game) == game_developer(game):
                embed.set_footer(text=f"{game_publisher(game)}")
            else:
                embed.set_footer(
                    text=f"{game_publisher(game)} | {game_developer(game)}"
                )

            # Only add the image if it's not empty
            if image_url:
                embed.set_image(image_url)

            # Add the game to the list of free games
            free_games.append(embed)

            # Save the game title to the previous games file so we don't
            # post it again
            with open(previous_games, "a+", encoding="utf-8") as file:
                file.write(f"{game_name}\n")

    return free_games


if __name__ == "__main__":
    get_free_epic_games()
