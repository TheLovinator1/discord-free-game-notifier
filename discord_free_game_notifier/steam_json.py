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

from discord_free_game_notifier.settings import app_dir, steam_icon
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
            # World of Tanks — A Present From Vinnie Pack
            {
                "id": "world_of_tanks_a_present_from_vinnie_pack",
                "game_name": "World of Tanks — A Present From Vinnie Pack",
                "game_url": "https://store.steampowered.com/app/2651870/World_of_Tanks__A_Present_From_Vinnie_Pack/",
                "start_date": datetime.datetime(2023, 12, 1, 11, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2024, 1, 8, 6, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_a_present_from_vinnie_pack.jpg",
                "description": 'Winter fun has arrived in World of Tanks! Grab Holiday Ops resources to upgrade your Festive Village and an eye-catching decal with this exclusive, time-limited Holiday Ops Gift Pack DLC! Add the bundle to your account for free to get 50 of each Holiday Ops resource (Meteoric Iron, Pure Emerald, Rock Crystal, and Warm Amber) and 3 "Present from Vinnie" decals.',  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
            # Warframe: Cumulus Collection
            {
                "id": "warframe_cumulus_collection",
                "game_name": "Warframe: Cumulus Collection",
                "game_url": "https://store.steampowered.com/app/2716340/Warframe_Cumulus_Collection/",
                "start_date": datetime.datetime(2023, 12, 18, 21, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2024, 1, 14, 21, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/warframe_cumulus_collection.jpg",
                "description": "Cirrus Armor Bundle, Cumulus Syandana, Stratus Pistol Skin, Spektaka Color Palette, and 3-day Resource Booster.",  # noqa: E501
                "developer": "Digital Extremes",
            },
            # World of Tanks — Snatch Gift Pack
            {
                "id": "world_of_tanks_snatch_gift_pack",
                "game_name": "World of Tanks — Snatch Gift Pack",
                "game_url": "https://store.steampowered.com/app/2749320/World_of_Tanks__Snatch_Gift_Pack/",
                "start_date": datetime.datetime(2024, 1, 11, 15, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2024, 1, 24, 0, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_snatch_gift_pack.jpg",
                "description": "The Snatch Gift Pack DLC includes:\n- 3 projection decals: Good Luck Charm\n- 3 Large Repair Kits\n- 3 Large First Aid Kits\n- 3 Automatic Fire Extinguishers",  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
            # World of Tanks Blitz - Bene Gesserit Pack
            {
                "id": "world_of_tanks_blitz_bene_gesserit_pack",
                "game_name": "World of Tanks Blitz - Bene Gesserit Pack",
                "game_url": "https://store.steampowered.com/app/2819910/World_of_Tanks_Blitz__Bene_Gesserit_Pack/",
                "start_date": datetime.datetime(2024, 2, 21, 19, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2024, 3, 7, 0, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_blitz_bene_gesserit_pack.jpg",
                "description": "The Bene Gesserit Pack includes:\n- Lady Jessica Profile Background\n- Bene Gesserit Epic avatar\n- Garage slot\n- 3 days of Premium Account\n- 5 certificates for x5 XP\n- 5 Epic Combat XP boosters",  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
            # World of Warships x Azur Lane: Free Intro Pack
            {
                "id": "world_of_warships_azur_lane_free_intro_pack",
                "game_name": "World of Warships x Azur Lane: Free Intro Pack",
                "game_url": "https://store.steampowered.com/app/2985620/World_of_Warships__Azur_Lane_Free_Intro_Pack/",
                "start_date": datetime.datetime(2025, 5, 16, 14, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2025, 6, 26, 0, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_azur_lane_free_intro_pack.jpg",
                "description": "The Azur Lane: Free Intro Pack includes:\n- 1x Azur Lane container\n- 5x “Azur Lane — Siren” expendable camouflages\n- Access to the Azur Lane Dorm Port",  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
            # World of Warships x Azur Lane — AL Avrora Free Unlock
            {
                "id": "world_of_warships_azur_lane_al_avrora_free_unlock",
                "game_name": "World of Warships x Azur Lane — AL Avrora Free Unlock",
                "game_url": "https://store.steampowered.com/app/2985560/World_of_Warships__Azur_Lane__AL_Avrora_Free_Unlock/",
                "start_date": datetime.datetime(2025, 5, 16, 14, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(2025, 6, 26, 0, 0, 0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_azur_lane_al_avrora_free_unlock.jpg",
                "description": "Play 5 battles to obtain:\n- AL Avrora - Tier III Premium Soviet cruiser\n- A Port slot\n- A Commander with 3 skill points trained for AL Avrora",  # noqa: E501
                "developer": "Wargaming Group Limited",
            },
        ],
    }

    # Check that each game has the required keys
    for game in free_games["free_games"]:
        required_keys: list[str] = [
            "id",
            "game_name",
            "game_url",
            "start_date",
            "end_date",
            "image_link",
            "description",
            "developer",
        ]
        for key in required_keys:
            if key not in game:
                logger.bind(game_name="Steam").error(f"Missing key: {key} in {game['game_name']}")
                return

    with Path.open(Path("pages/steam.json"), "w", encoding="utf-8") as file:
        json.dump(free_games, file, indent=4)
        logger.bind(game_name="Steam").info("Created/updated steam.json")


def get_json() -> dict:
    """Gets a json file from the json folder.

    Returns:
        dict: The json file as a dict.
    """
    json_location: str = "https://thelovinator1.github.io/discord-free-game-notifier/steam.json"
    json_file: dict = {}

    try:
        json_file = requests.get(json_location, timeout=30).json()
    except requests.exceptions.ConnectionError:
        logger.bind(game_name="Steam").error("Unable to connect to github.com")

    logger.bind(game_name="Steam").debug("Got steam.json\n{}", json_file)
    return json_file


def scrape_steam_json() -> Generator[DiscordEmbed, Any, list[Any] | None]:
    """Get the free games from steam.json.

    Yields:
        Generator[DiscordEmbed, Any, list[Any] | None]: A list of embeds containing the free games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(app_dir) / "steam.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Check steam.json if free games
    steam_json: dict = get_json()

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
        developer: str = _game["developer"]

        # When the giveaway starts
        start_date: str = _game["start_date"] or datetime.datetime.now(tz=datetime.UTC).isoformat()
        start_date_unix: int = int(datetime.datetime.fromisoformat(start_date).timestamp())

        # When the giveaway ends
        end_date: str = _game["end_date"] or datetime.datetime.now(tz=datetime.UTC).isoformat()
        end_date_unix: int = int(datetime.datetime.fromisoformat(end_date).timestamp())

        # Check if the game has already been posted
        if already_posted(previous_games, game_id):
            continue

        # Check if the game is still free

        current_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
        if end_date_unix < current_time:
            logger.info(f"{game_name} is no longer free")
            continue

        # Create the embed and add it to the list of free games.
        embed = DiscordEmbed(description=description)
        embed.set_author(
            name=f"{game_name}",
            url=game_url,
            icon_url=steam_icon,
        )
        if image_url:
            embed.set_image(url=image_url)
        embed.set_timestamp()
        embed.add_embed_field(name="Start", value=f"<t:{start_date_unix}:R>")
        embed.add_embed_field(name="End", value=f"<t:{end_date_unix}:R>")
        embed.set_footer(text=developer)

        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_id}\n")

        yield embed


if __name__ == "__main__":
    create_json_file()
    for game in scrape_steam_json():
        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                f"Error when checking game for Steam (JSON):\n{response.status_code} - {response.reason}: {response.text}",  # noqa: E501
            )
