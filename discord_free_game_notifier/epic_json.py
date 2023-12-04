"""Check https://thelovinator1.github.io/discord-free-game-notifier/epic.json for free games.

This is for games that are not found by epic.py.
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
    """Create or overwrite the Epic.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    free_games: dict[str, list[dict[str, str]]] = {
        "free_games": [
            {
                "id": "the_sims_4_my_first_pet_stuff",
                "game_name": "The Sims™ 4 My First Pet Stuff",
                "game_url": "https://store.epicgames.com/en-US/p/the-sims-4--my-first-pet-stuff",
                "start_date": datetime.datetime(
                    2023,
                    12,
                    1,
                    11,
                    0,
                    0,
                    tzinfo=datetime.UTC,
                ).isoformat(),
                "end_date": datetime.datetime(
                    2024,
                    1,
                    9,
                    18,
                    0,
                    0,
                    tzinfo=datetime.UTC,
                ).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/the_sims_4_my_first_pet_stuff.jpg",
                "description": "Welcome home a new small animal and show love for Cats and Dogs with The Sims™ 4 My First Pet Stuff.\n\n[Instant Checkout](https://store.epicgames.com/purchase?offers=1-2a14cf8a83b149919a2399504e5686a6-7002cdb1eb2543da85ac8a3c4c6d71d5#/)",  # noqa: E501
                "developer": "Maxis",
            },
        ],
    }

    with Path.open(Path("pages/epic.json"), "w", encoding="utf-8") as file:
        json.dump(free_games, file, indent=4)
        logger.bind(game_name="Epic").info("Created/updated epic.json")


def get_json() -> dict:
    """Gets a json file from the json folder.

    Returns:
        dict: The json file as a dict.
    """
    json_location: str = "https://thelovinator1.github.io/discord-free-game-notifier/epic.json"
    json_file: dict = {}

    try:
        json_file = requests.get(json_location, timeout=30).json()
    except requests.exceptions.ConnectionError:
        logger.bind(game_name="Epic").error("Unable to connect to github.com")

    logger.bind(game_name="Epic").debug("Got epic.json\n{}", json_file)
    return json_file


def scrape_epic_json() -> Generator[DiscordEmbed, Any, list[Any] | None]:
    """Get the free games from Epic.json.

    Yields:
        Generator[DiscordEmbed, Any, list[Any] | None]: A list of embeds containing the free games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "epic.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Check Epic.json if free games
    epic_json = get_json()

    # If Epic.json is empty, return an empty list
    if not epic_json:
        return []

    # Get the free games from Epic.json
    free_games = epic_json["free_games"]

    for _game in free_games:
        game_id: str = _game["id"]
        game_name: str = _game["game_name"]
        description: str = _game["description"]
        game_url: str = _game["game_url"]
        image_url: str = _game["image_link"]
        start_date: str = _game["start_date"]
        developer: str = _game["developer"]
        unix_start_date: int = int(
            datetime.datetime.fromisoformat(start_date).timestamp(),
        )
        end_date: str = _game["end_date"]
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
        embed.set_author(
            name=f"{game_name}",
            url=game_url,
            icon_url=settings.epic_icon,
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
    for game in scrape_epic_json():
        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                f"Error when checking game for Epic (JSON):\n{response.status_code} - {response.reason}: {response.text}",  # noqa: E501
            )
