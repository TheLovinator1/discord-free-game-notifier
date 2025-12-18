"""Test embeds from JSON files in Discord.

This module provides a way to test and preview embeds generated from JSON files
without waiting for the scheduled checks. Useful for validating embed formatting
and testing webhook configuration. Loads from local JSON files instead of GitHub.

Usage:
    python -m discord_free_game_notifier.test_embeds [service] [index]

Examples:
    python -m discord_free_game_notifier.test_embeds epic
    python -m discord_free_game_notifier.test_embeds steam 0
    python -m discord_free_game_notifier.test_embeds all
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from discord_webhook import DiscordEmbed
from loguru import logger
from pydantic import ValidationError

from discord_free_game_notifier import epic_json
from discord_free_game_notifier import epic_mobile
from discord_free_game_notifier import steam_json
from discord_free_game_notifier import webhook

MIN_ARGV_LENGTH = 2
INDEX_ARGV_POSITION = 2


def _load_epic_games_from_local_json() -> list[tuple[DiscordEmbed, str]] | None:
    """Load Epic games from local pages/epic.json file.

    Returns:
        List of tuples containing (DiscordEmbed, game_id) or None if error.
    """
    try:
        epic_json_path = Path("pages/epic.json")
        if not epic_json_path.exists():
            logger.error(f"Epic JSON file not found at {epic_json_path.absolute()}")
            return None

        with epic_json_path.open(encoding="utf-8") as file:
            data = json.load(file)

        epic_games: epic_json.EpicFreeGames = epic_json.EpicFreeGames.model_validate(data)
        free_games: list[epic_json.EpicGame] = epic_games.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            unix_start_date = int(game.start_date.timestamp())
            unix_end_date = int(game.end_date.timestamp())

            embed = DiscordEmbed(description=game.description)

            if game.image_link is not None:
                embed.set_image(url=str(game.image_link))

            embed.set_timestamp()
            embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
            embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
            embed.set_footer(text=game.developer)

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Epic.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading Epic games from local JSON: {e}")
        return None
    else:
        return notified_games


def _load_epic_mobile_games_from_local_json() -> list[tuple[DiscordEmbed, str]] | None:
    """Load Epic Mobile games from local pages/epic_mobile.json file.

    Returns:
        List of tuples containing (DiscordEmbed, game_id) or None if error.
    """
    try:
        epic_mobile_json_path = Path("pages/epic_mobile.json")
        if not epic_mobile_json_path.exists():
            logger.error(f"Epic Mobile JSON file not found at {epic_mobile_json_path.absolute()}")
            return None

        with epic_mobile_json_path.open(encoding="utf-8") as file:
            data = json.load(file)

        epic_mobile_games: epic_mobile.EpicMobileFreeGames = epic_mobile.EpicMobileFreeGames.model_validate(data)
        free_games: list[epic_mobile.EpicMobileGame] = epic_mobile_games.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            unix_start_date = int(game.start_date.timestamp())
            unix_end_date = int(game.end_date.timestamp())

            embed = DiscordEmbed(description=game.description)

            if game.image_link is not None:
                embed.set_image(url=str(game.image_link))

            embed.set_timestamp()
            embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
            embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
            embed.set_footer(text=game.developer)

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Epic.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading Epic Mobile games from local JSON: {e}")
        return None
    else:
        return notified_games


def _load_steam_games_from_local_json() -> list[tuple[DiscordEmbed, str]] | None:
    """Load Steam games from local pages/steam.json file.

    Returns:
        List of tuples containing (DiscordEmbed, game_id) or None if error.
    """
    try:
        steam_json_path = Path("pages/steam.json")
        if not steam_json_path.exists():
            logger.error(f"Steam JSON file not found at {steam_json_path.absolute()}")
            return None

        with steam_json_path.open(encoding="utf-8") as file:
            data: dict[str, steam_json.SteamGame] = json.load(file)

        steam_games: steam_json.SteamFreeGames = steam_json.SteamFreeGames.model_validate(data)
        free_games: list[steam_json.SteamGame] = steam_games.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            unix_start_date = int(game.start_date.timestamp())
            unix_end_date = int(game.end_date.timestamp())

            embed = DiscordEmbed(description=game.description)

            if game.image_link is not None:
                embed.set_image(url=str(game.image_link))

            embed.set_timestamp()
            embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
            embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
            embed.set_footer(text=game.developer)

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Steam.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading Steam games from local JSON: {e}")
        return None
    else:
        return notified_games


def send_epic_embeds(index: int | None = None) -> None:
    """Send Epic Games JSON embeds to Discord (from local file).

    Args:
        index: Optional index of specific game to send. If None, sends all games.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = _load_epic_games_from_local_json()

    if not free_games:
        logger.warning("No Epic Games found in local JSON")
        return

    games_to_test: list[tuple[DiscordEmbed, str]] = [free_games[index]] if index is not None else free_games

    for embed, game_id in games_to_test:
        logger.info(f"Sending test Epic embed for {game_id}")
        webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.EPIC)


def send_steam_embeds(index: int | None = None) -> None:
    """Send Steam JSON embeds to Discord (from local file).

    Args:
        index: Optional index of specific game to send. If None, sends all games.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = _load_steam_games_from_local_json()

    if not free_games:
        logger.warning("No Steam Games found in local JSON")
        return

    games_to_test: list[tuple[DiscordEmbed, str]] = [free_games[index]] if index is not None else free_games

    for embed, game_id in games_to_test:
        logger.info(f"Sending test Steam embed for {game_id}")
        webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.STEAM)


def send_epic_mobile_embeds(index: int | None = None) -> None:
    """Send Epic Games Mobile JSON embeds to Discord (from local file).

    Args:
        index: Optional index of specific game to send. If None, sends all games.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = _load_epic_mobile_games_from_local_json()

    if not free_games:
        logger.warning("No Epic Mobile Games found in JSON")
        return

    games_to_test: list[tuple[DiscordEmbed, str]] = [free_games[index]] if index is not None else free_games

    for embed, game_id in games_to_test:
        logger.info(f"Sending test Epic Mobile embed for {game_id}")
        webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.EPIC)


def main() -> None:
    """Main function to test embeds from JSON files.

    Usage:
        python -m discord_free_game_notifier.test_embeds [service] [index]

    Services: epic, steam, epic_mobile, all
    Index: Optional specific game index (0-based)
    """
    if len(sys.argv) < MIN_ARGV_LENGTH:
        logger.info("Usage: python -m discord_free_game_notifier.test_embeds [service] [index]")
        logger.info("Services: epic, steam, epic_mobile, all")
        logger.info("Index: Optional specific game index (0-based)")
        return

    service: str = sys.argv[1].lower()
    index: int | None = None

    if len(sys.argv) > INDEX_ARGV_POSITION:
        try:
            index = int(sys.argv[INDEX_ARGV_POSITION])
        except ValueError:
            logger.error(f"Invalid index: {sys.argv[INDEX_ARGV_POSITION]}. Must be an integer.")
            return

    if service == "epic":
        send_epic_embeds(index)
    elif service == "steam":
        send_steam_embeds(index)
    elif service == "epic_mobile":
        send_epic_mobile_embeds(index)
    elif service == "all":
        send_epic_embeds()
        send_steam_embeds()
        send_epic_mobile_embeds()
    else:
        logger.error(f"Unknown service: {service}")
        logger.info("Supported services: epic, steam, epic_mobile, all")


if __name__ == "__main__":
    main()
