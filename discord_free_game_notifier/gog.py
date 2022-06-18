import os
import re
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"  # noqa: E501


def already_posted(previous_games, game_name) -> bool:
    # Check if the game has already been posted
    if os.path.isfile(previous_games):
        with open(previous_games, "r", encoding="utf-8") as file:
            if game_name in file.read():
                settings.logger.debug(
                    "\tHas already been posted before. Skipping!",
                )
                return True
    return False


def get_game_name(banner_title_text: str):
    print(banner_title_text)
    result = re.search(
        r"being with us! Claim (.*?) as a token of our gratitude!",
        banner_title_text,
    )
    if result:
        return result.group(1)
    return "GOG Giveaway"


def create_embed(
    free_games,
    previous_games,
    game_name: str,
    game_url: str,
    image_url: str,
):
    embed = DiscordEmbed(
        description=f"[Click here to claim {game_name}!](https://www.gog.com/giveaway/claim)"
    )
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


def get_free_gog_games() -> List[DiscordEmbed]:
    """Get a list of free GOG games.

    Returns:
        List[DiscordEmbed]: List of Embeds containing the free GOG games.
    """

    # Save previous free games to a file so we don't post the same games again
    previous_games: Path = Path(settings.app_dir) / "gog.txt"
    settings.logger.debug(f"Previous games file: {previous_games}")

    # Create file if it doesn't exist
    if not os.path.exists(previous_games):
        open(previous_games, "w", encoding="utf-8").close()

    # List of dictionaries containing Embeds to send to Discord
    free_games: List[DiscordEmbed] = []

    request = requests.get("https://www.gog.com/")
    soup = BeautifulSoup(request.text, "html.parser")
    giveaway = soup.find("a", {"id": "giveaway"})

    # If there is no giveaway, return an empty list
    if giveaway is None:
        return free_games

    # Game name
    banner_title = giveaway.find("span", class_="giveaway-banner__title")
    game_name = get_game_name(banner_title.text)

    # Game URL
    ng_href = giveaway.attrs["ng-href"]
    game_url = f"https://www.gog.com{ng_href}"
    settings.logger.debug(f"\tURL: {game_url}")

    # Game image
    image_url_class = giveaway.find("source", attrs={"srcset": True})
    image_url: str = image_url_class.attrs["srcset"].strip().split()
    image_url = f"https:{image_url[0]}"
    settings.logger.debug(f"\tImage URL: {image_url}")

    # Check if the game has already been posted
    if already_posted(previous_games, game_name):
        return free_games

    # Create the embed and add it to the list of free games
    create_embed(
        free_games=free_games,
        previous_games=previous_games,
        game_name=game_name,
        game_url=game_url,
        image_url=image_url,
    )

    return free_games


if __name__ == "__main__":
    # Remember to delete previous games if you are testing
    # It can be found in %appdata%\TheLovinator\discord_free_game_notifier
    get_free_gog_games()
