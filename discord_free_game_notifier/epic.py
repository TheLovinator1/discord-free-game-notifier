import datetime
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
    previous_games: Path = Path(Settings.app_dir) / "epic.txt"

    # HTTP params for the US free games
    free_games_params = {"locale": "en-US", "country": "US", "allowCountries": "US"}

    # Epic's backend API URL for the free games promotion
    epic_api_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

    # backend API request
    response = requests.get(epic_api_url, params=free_games_params)

    # list of dictionaries containing information about the free games
    free_games: List[Embed] = []

    # find the free games in the response
    for game in response.json()["data"]["Catalog"]["searchStore"]["elements"]:
        if datetime.datetime.now() < datetime.datetime.strptime(game["effectiveDate"], "%Y-%m-%dT%H:%M:%S.%fZ"):
            if game["title"] != "Mystery Game":
                for promotion in game["promotions"]["promotionalOffers"]:
                    for offer in promotion["promotionalOffers"]:
                        start_date = int(time.mktime(time.strptime(offer["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))
                        end_date = int(time.mktime(time.strptime(offer["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ")))

                if os.path.isfile(previous_games):
                    with open(previous_games, "r") as f:
                        if game["title"] in f.read():
                            break

                for image in game["keyImages"]:
                    if image["type"] == "DieselStoreFrontWide":
                        image_url = image["url"]

                game_url = f"https://www.epicgames.com/store/en-US/p/{game['productSlug']}"

                embed = Embed(description=game["description"], color=0xFFFFFF, timestamp="now")
                embed.set_author(
                    name=game["title"],
                    url=game_url,
                    icon_url="https://lovinator.space/Epic_Games_logo.png",
                )
                embed.add_field(name="Start", value=f"<t:{start_date}:R>")
                embed.add_field(name="End", value=f"<t:{end_date}:R>")
                embed.set_footer(text=game["seller"]["name"])
                embed.set_image(image_url)
                free_games.append(embed)

                with open(previous_games, "a") as f:
                    f.write(f"{game['title']}\n")

    return free_games
