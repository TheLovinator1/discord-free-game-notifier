import os
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"  # noqa: E501
GOG_URL = "https://www.gog.com/en/games?priceRange=0,0&order=desc:discount&discounted=true&showDLCs=true"  # noqa: E501, pylint: disable=line-too-long


def get_free_gog_games() -> List[DiscordEmbed]:
    """Get a list of free GOG games.

    Returns:
        List[DiscordEmbed]: List of Embeds containing the free GOG games.
    """
    image_url: str = ""

    # Save previous free games to a file so we don't post the same games again
    previous_games: Path = Path(settings.app_dir) / "gog.txt"
    settings.logger.debug(f"Previous games file: {previous_games}")

    # Create file if it doesn't exist
    if not os.path.exists(previous_games):
        open(previous_games, "w", encoding="utf-8").close()

    # List of dictionaries containing Embeds to send to Discord
    free_games: List[DiscordEmbed] = []

    request = requests.get(GOG_URL)
    soup = BeautifulSoup(request.text, "html.parser")
    games = soup.find_all("a", {"selenium-id": "productTile"})
    for game in games:
        game_name_class = game.find(
            "p",
            {"selenium-id": "productTileGameTitle"},
        )
        game_name = game_name_class["title"]
        settings.logger.debug(f"Game: {game_name}")

        game_url = game["href"]
        settings.logger.debug(f"\tURL: {game_url}")

        image_url_class = game.find("source", attrs={"srcset": True})
        image_url = image_url_class["srcset"].split(",")[0].split(" ")[0]
        image_url = image_url.replace("_product_tile_300w.webp", ".webp")
        settings.logger.debug(f"\tImage URL: {image_url}")

        # Check if the game has already been posted
        if os.path.isfile(previous_games):
            with open(previous_games, "r", encoding="utf-8") as file:
                if game_name in file.read():
                    settings.logger.debug(
                        "\tHas already been posted before. Skipping!",
                    )
                    continue

            embed = DiscordEmbed(color=0xFFFFFF, timestamp="now")
            embed.set_author(
                name=game_name,
                url=game_url,
                icon_url="https://lovinator.space/gog_logo.png",
            )

            # Only add the image if it's not empty
            if image_url:
                embed.set_image(url=image_url)

            # Add the game to the list of free games
            free_games.append(embed)

            # Save the game title to the previous games file so we don't
            # post it again
            with open(previous_games, "a+", encoding="utf-8") as file:
                file.write(f"{game_name}\n")

    return free_games


if __name__ == "__main__":
    # Remember to delete previous games if you are testing
    # It can be found in %appdata%\TheLovinator\discord_free_game_notifier
    get_free_gog_games()
