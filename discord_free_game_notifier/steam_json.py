"""Check https://thelovinator1.github.io/discord-free-game-notifier/steam.json for free games.

This is for games that are not found by steam.py.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from discord_webhook import DiscordEmbed
from loguru import logger

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

if TYPE_CHECKING:
    from collections.abc import Generator


def create_json_file() -> None:
    """Create or overwrite the steam.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    free_games: dict[str, list[dict[str, str]]] = {
        "free_games": [
            {
                "id": "world_of_tanks_a_present_from_vinnie_pack",
                "game_name": "World of Tanks — A Present From Vinnie Pack",
                "game_url": "https://store.steampowered.com/app/2651870/World_of_Tanks__A_Present_From_Vinnie_Pack/",
                "start_date": datetime.datetime(
                    2023, 12, 1, 11, 0, 0, tzinfo=datetime.UTC
                ).isoformat(),
                "end_date": datetime.datetime(
                    2024, 1, 8, 6, 0, 0, tzinfo=datetime.UTC
                ).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_a_present_from_vinnie_pack.jpg",
                "description": 'Winter fun has arrived in World of Tanks! Grab Holiday Ops resources to upgrade your Festive Village and an eye-catching decal with this exclusive, time-limited Holiday Ops Gift Pack DLC! Add the bundle to your account for free to get 50 of each Holiday Ops resource (Meteoric Iron, Pure Emerald, Rock Crystal, and Warm Amber) and 3 "Present from Vinnie" decals.',  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
        ],
    }

    with Path.open(Path("pages/steam.json"), "w", encoding="utf-8") as file:
        json.dump(free_games, file, indent=4)
        logger.bind(game_name="Steam").info("Created/updated steam.json")


def get_json() -> dict:
    """Gets a json file from the json folder.

    Returns:
        dict: The json file as a dict.
    """
    json_location: str = (
        "https://thelovinator1.github.io/discord-free-game-notifier/steam.json"
    )
    json_file: dict = {}

    try:
        json_file = requests.get(json_location, timeout=30).json()
    except requests.exceptions.ConnectionError:
        logger.bind(game_name="Steam").error("Unable to connect to github.com")

    logger.bind(game_name="Steam").debug("Got steam.json\n{}", json_file)
    return json_file


def get_steam_free_games() -> Generator[DiscordEmbed, Any, list[Any] | None]:
    """Get the free games from steam.json.

    Yields:
        Generator[DiscordEmbed, Any, list[Any] | None]: A list of embeds containing the free games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "Steam.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Check steam.json if free games
    steam_json = get_json()

    # If steam.json is empty, return an empty list
    if not steam_json:
        return []

    # Get the free games from steam.json
    free_games = steam_json["free_games"]

    for _game in free_games:
        game_id: str = _game["id"]
        game_name: str = _game["game_name"]
        description: str = _game["description"]
        game_url: str = _game["game_url"]
        image_url: str = _game["image_link"]
        start_date: str = _game["start_date"]
        developer: str = _game["developer"]
        unix_start_date: int = int(
            datetime.datetime.fromisoformat(start_date).timestamp()
        )
        end_date: str = _game["end_date"]
        unix_end_date: int = int(datetime.datetime.fromisoformat(end_date).timestamp())

        # Check if the game has already been posted
        if already_posted(previous_games, game_id):
            continue

        # Create the embed and add it to the list of free games.
        embed = DiscordEmbed(description=description)
        embed.set_author(
            name=f"Free game: {game_name}", url=game_url, icon_url=settings.steam_icon
        )
        embed.set_image(url=image_url)
        embed.set_timestamp()
        embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
        embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
        embed.set_footer(text=developer)

        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_id}\n")

        yield embed


if __name__ == "__main__":
    create_json_file()
    for game in get_steam_free_games():
        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                f"Error when checking game for Steam (JSON):\n{response.status_code} - {response.reason}: {response.text}",  # noqa: E501
            )
