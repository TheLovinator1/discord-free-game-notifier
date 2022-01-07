import os
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from dhooks import Embed

from discord_free_game_notifier.settings import Settings

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"


def get_free_steam_games() -> List[Embed]:
    image_url: str = ""

    # Save previous free games to a file so we don't post the same games again
    previous_games: Path = Path(Settings.app_dir) / "steam.txt"
    Settings.logger.debug(f"Previous games file: {previous_games}")

    # Create file if it doesn't exist
    if not os.path.exists(previous_games):
        open(previous_games, "w").close()

    # List of dictionaries containing Embeds to send to Discord
    free_games: List[Embed] = []

    r = requests.get("https://store.steampowered.com/search/?maxprice=free&specials=1")
    soup = BeautifulSoup(r.text, "html.parser")
    games = soup.find_all("div", {"id": "search_resultsRows"})
    for game in games:
        game_name_class = game.find("span", class_="title")
        game_name = game_name_class.text
        Settings.logger.debug(f"Game: {game_name}")

        for link in soup.find_all("a", class_="search_result_row"):
            game_url = link.get("href")
            game_id = link.get("data-ds-appid")
            Settings.logger.debug(f"\tURL: {game_url}")

        image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game_id}/header.jpg"

        # Check if the game has already been posted
        if os.path.isfile(previous_games):
            with open(previous_games, "r") as f:
                if game_name in f.read():
                    Settings.logger.debug("\tHas already been posted before. Skipping!")
                    continue

            # TODO: Implement description
            embed = Embed(description="Hello", color=0xFFFFFF, timestamp="now")
            embed.set_author(
                name=game_name,
                url=game_url,
                icon_url="https://lovinator.space/Steam_logo.png",
            )

            # Only add the image if it's not empty
            if image_url:
                embed.set_image(image_url)

            # Add the game to the list of free games
            free_games.append(embed)

            # Save the game title to the previous games file so we don't post it again
            with open(previous_games, "a+") as f:
                f.write(f"{game_name}\n")

    return free_games


if __name__ == "__main__":
    get_free_steam_games()
