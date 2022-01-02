"""Modified version of https://github.com/andrewguest/slack-free-epic-games"""
import os
import time
from pathlib import Path
from typing import Dict, List

import requests
from dhooks import Embed

from settings import Settings


def get_free_epic_games() -> List[Embed]:
    """Uses an API from Epic to parse a list of free games to find this week's free games.

    Original source: https://github.com/andrewguest/slack-free-epic-games/blob/main/lambda_function.py#L18
    image_url = ""
    start_date = 0
    end_date = 0

    Returns:
        List[Embed]: List of Embeds that will be sent to Discord.
    """
    # Save previous free games to a file so we don't post the same games again
    previous_games: Path = Path(Settings.app_dir) / "epic.txt"
    Settings.logger.debug(f"Previous games file: {previous_games}")

    # HTTP params for the US free games
    free_games_params: Dict[str, str] = {"locale": "en-US", "country": "US", "allowCountries": "US"}

    # Epic's backend API URL for the free games promotion
    epic_api_url: str = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

    # Connect to the Epic API and get the free games
    response = requests.get(epic_api_url, params=free_games_params)

    # List of dictionaries containing Embeds to send to Discord
    free_games: List[Embed] = []

    # Find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        game_name = game["title"]
        original_price = game["price"]["totalPrice"]["originalPrice"]
        discount = game["price"]["totalPrice"]["discount"]

        # Check if the original price and the discount is equal and that the game is not free to play
        if (original_price - discount) == 0 and (original_price != 0 and discount != 0):
            Settings.logger.debug(f"Game: {game_name}")
            Settings.logger.debug(f"\tPrice: {original_price/100}$")
            Settings.logger.debug(f"\tDiscount: {discount/100}$")
            if game["promotions"]:
                for promotion in game["promotions"]["promotionalOffers"]:
                    for offer in promotion["promotionalOffers"]:
                        start_date = int(time.mktime(time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        end_date = int(time.mktime(time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        Settings.logger.debug(f"\tStarted: {start_date}")
                        Settings.logger.debug(f"\tEnds in: {end_date}")
            else:
                Settings.logger.debug(f"\tNo promotions found for {game['title']}, skipping")
                continue

            # Check if the game has already been posted
            if os.path.isfile(previous_games):
                with open(previous_games, "r") as f:
                    if game_name in f.read():
                        Settings.logger.debug("\tHas already been posted before. Skipping!")
                        continue

            # Get the game's image. Image is 2560x1440
            for image in game["keyImages"]:
                if image["type"] == "DieselStoreFrontWide":
                    image_url = image["url"]
                    Settings.logger.debug(f"\tImage URL: {image_url}")

            # If you click the game name in Discord, you'll be taken to the game's page on Epic
            game_url = f"https://www.epicgames.com/store/en-US/p/{game['productSlug']}"
            Settings.logger.debug(f"\tURL: {game_url}")

            embed = Embed(description=game["description"], color=0xFFFFFF, timestamp="now")
            embed.set_author(
                name=game_name,
                url=game_url,
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
            embed.add_field(name="Start", value=f"<t:{start_date}:R>")
            embed.add_field(name="End", value=f"<t:{end_date}:R>")
            embed.set_footer(text=game["seller"]["name"])
            # Only add the image if it's not empty
            if image_url:
                embed.set_image(image_url)

            # Add the game to the list of free games
            free_games.append(embed)

            # Save the game title to the previous games file so we don't post it again
            with open(previous_games, "a") as f:
                f.write(f"{game_name}\n")

    return free_games
