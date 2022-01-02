import os
import time
from pathlib import Path
from typing import List

import requests
from dhooks import Embed

from settings import Settings


def get_free_epic_games() -> List[Embed]:
    """Uses an API from Epic to parse a list of free games to find this week's free games.

    Modified version of https://github.com/andrewguest/slack-free-epic-games"""
    image_url = ""
    start_date = 0
    end_date = 0

    previous_games: Path = Path(Settings.app_dir) / "epic.txt"
    Settings.logger.debug(f"Previous games file: {previous_games}")

    # HTTP params for the US free games
    free_games_params = {"locale": "en-US", "country": "US", "allowCountries": "US"}

    # Epic's backend API URL for the free games promotion
    epic_api_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

    # backend API request
    response = requests.get(epic_api_url, params=free_games_params)
    # Settings.logger.debug(f"Response: {response}")

    # list of dictionaries containing information about the free games
    free_games: List[Embed] = []

    # find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        original_price = game["price"]["totalPrice"]["originalPrice"]
        discount = game["price"]["totalPrice"]["discount"]

        # Check if the original price and the discount is equal and that the game is not free to play
        if (original_price - discount) == 0 and (original_price != 0 and discount != 0):
            Settings.logger.debug(f"Game: {game['title']}")
            Settings.logger.debug(f"\tPrice: {original_price/100}€")
            Settings.logger.debug(f"\tDiscount: {discount/100}€")
            if game["promotions"]:
                for promotion in game["promotions"]["promotionalOffers"]:
                    for offer in promotion["promotionalOffers"]:
                        start_date = int(time.mktime(time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        end_date = int(time.mktime(time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        Settings.logger.debug(f"\tStart date: {start_date}")
                        Settings.logger.debug(f"\tEnd date: {end_date}")
            else:
                Settings.logger.debug(f"\tNo promotions found for {game['title']}, skipping")
                continue

            if os.path.isfile(previous_games):
                with open(previous_games, "r") as f:
                    if game["title"] in f.read():
                        Settings.logger.debug("\tHas already been posted before. Skipping!")
                        continue

            for image in game["keyImages"]:
                if image["type"] == "DieselStoreFrontWide":
                    image_url = image["url"]
                    Settings.logger.debug(f"\tImage URL: {image_url}")

            game_url = f"https://www.epicgames.com/store/en-US/p/{game['productSlug']}"
            Settings.logger.debug(f"\tURL: {game_url}")

            embed = Embed(description=game["description"], color=0xFFFFFF, timestamp="now")
            embed.set_author(
                name=game["title"],
                url=game_url,
                icon_url="https://lovinator.space/Epic_Games_logo.png",
            )

            embed.add_field(name="Start", value=f"<t:{start_date}:R>")
            embed.add_field(name="End", value=f"<t:{end_date}:R>")
            embed.set_footer(text=game["seller"]["name"])
            if image_url:
                embed.set_image(image_url)

            free_games.append(embed)

            with open(previous_games, "a") as f:
                f.write(f"{game['title']}\n")

    return free_games
