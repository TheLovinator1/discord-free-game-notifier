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
    """Create or overwrite the ubisoft.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    free_games: dict[str, list[dict[str, str]]] = {
        "free_games": [
            {
                "id": "ac_syndicate",
                "game_name": "Assassin's Creed Syndicate",
                "game_url": "https://register.ubisoft.com/acsyndicate/",
                "start_date": datetime.datetime(2023, 11, 27, 13, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2023, 12, 6, 13, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/ac_syndicate.png",
                "description": "London, 1868. In the heart of the Industrial Revolution, lead your underworld organization and grow your influence to fight those who exploit the less privileged in the name of progress.",  # noqa: E501
            },
        ],
    }

    with Path.open(Path("pages/ubisoft.json"), "w", encoding="utf-8") as file:
        json.dump(free_games, file, indent=4)
        logger.bind(game_name="Ubisoft").info("Created/updated ubisoft.json")


def get_json() -> dict:
    """Gets a json file from the json folder.

    Returns:
        dict: The json file as a dict.
    """
    json_location: str = "https://thelovinator1.github.io/discord-free-game-notifier/ubisoft.json"
    json_file: dict = {}

    try:
        json_file = requests.get(json_location, timeout=30).json()
    except requests.exceptions.ConnectionError:
        logger.bind(game_name="Ubisoft").error("Unable to connect to github.com")

    logger.bind(game_name="Ubisoft").debug("Got ubisoft.json\n{}", json_file)
    return json_file


def get_ubisoft_free_games() -> Generator[DiscordEmbed, Any, list[Any] | None]:
    """Get the free games from ubisoft.json.

    Yields:
        Generator[DiscordEmbed, Any, list[Any] | None]: A list of embeds containing the free games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "ubisoft.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Check ubisoft.json if free games
    ubisoft_json = get_json()

    # If ubisoft.json is empty, return an empty list
    if not ubisoft_json:
        return []

    # Get the free games from ubisoft.json
    free_games = ubisoft_json["free_games"]

    for game in free_games:
        game_id: str = game["id"]
        game_name: str = game["game_name"]
        description: str = game["description"]
        game_url: str = game["game_url"]
        image_url: str = game["image_link"]
        start_date: str = game["start_date"]
        unix_start_date: int = int(datetime.datetime.fromisoformat(start_date).timestamp())
        end_date: str = game["end_date"]
        unix_end_date: int = int(datetime.datetime.fromisoformat(end_date).timestamp())

        # Check if the game has already been posted
        if already_posted(previous_games, game_id):
            continue

        # Check if the game is still free
        current_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
        if unix_end_date < current_time:
            logger.info(f"{game_name} is no longer free")
            continue

        # Create the embed and add it to the list of free games.
        embed = DiscordEmbed(description=description)
        embed.set_author(name=f"{game_name}", url=game_url, icon_url=settings.ubisoft_icon)
        embed.set_image(url=image_url)
        embed.set_timestamp()
        embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
        embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
        embed.set_footer(text="Ubisoft")

        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_id}\n")

        yield embed


if __name__ == "__main__":
    create_json_file()
    for game in get_ubisoft_free_games():
        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                f"Error when checking game for Ubisoft:\n{response.status_code} - {response.reason}: {response.text}",
            )
