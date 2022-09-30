import os
from pathlib import Path
from typing import Any, Generator

import bs4
import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings
from discord_free_game_notifier.webhook import send_embed_webhook

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
STEAM_URL = "https://store.steampowered.com/search/?maxprice=free&specials=1"


def get_free_steam_games() -> Generator[DiscordEmbed, Any, None]:
    """Go to the Steam store and check for free games and return them.

    Returns:
        Embed containing the free Steam games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "steam.txt"
    settings.logger.debug(f"Previous games file: {previous_games}")

    # Create the file if it doesn't exist-
    if not os.path.exists(previous_games):
        open(previous_games, "w", encoding="utf-8").close()

    request = requests.get(STEAM_URL)
    soup = BeautifulSoup(request.text, "html.parser")

    games = soup.find_all("a", class_="search_result_row")
    for game in games:
        embed = DiscordEmbed()
        game_name: str = get_game_name(game)
        game_url: str = get_game_url(game)
        image_url: str = get_game_image(game)

        # Check if the game has already been posted
        if os.path.isfile(previous_games):
            with open(previous_games, "r", encoding="utf-8") as file:
                if game_name in file.read():
                    settings.logger.debug(f"{previous_games} has already been posted before. Skipping!")
                    continue

        embed.set_author(name=game_name, url=game_url, icon_url=settings.steam_image_url)
        embed.set_image(url=image_url)

        # Save the game title to the previous games file, so we don't post it again.
        with open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_name}\n")

        yield embed
    return


def get_game_image(game):
    """
    Get the game ID and create image URL.

    Args:
        game: Contains information about the game.

    Returns:
        Image url for the game.
    """
    game_id = game["data-ds-appid"]
    image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game_id}/header.jpg"
    settings.logger.debug(f"\tImage: {image_url}")
    return image_url


def get_game_url(game):
    """
    Get the game url.

    Args:
        game: Contains information about the game.

    Returns:
        Game URL.
    """
    game_url = game["href"]
    settings.logger.debug(f"\tURL: {game_url}")
    return game_url


def get_game_name(game):
    """
    Get the game name.

    Args:
        game: Contains information about the game.

    Returns:
        The game name.
    """
    game_name_class: bs4.element.Tag = game.find("span", class_="title")
    game_name = game_name_class.text
    settings.logger.debug(f"Game: {game_name}")
    return game_name


if __name__ == "__main__":
    # Remember to delete previous games if you are testing
    # It can be found in %appdata%\TheLovinator\discord_free_game_notifier
    for free_game in get_free_steam_games():
        response = send_embed_webhook(free_game)
        if not response.ok:
            print(
                f"Error when checking game for Steam:\n{response.status_code} - {response.reason}: {response.text}")
