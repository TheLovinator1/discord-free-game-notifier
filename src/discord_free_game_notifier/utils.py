from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from discord_free_game_notifier import settings

if TYPE_CHECKING:
    from discord_free_game_notifier.webhook import GameService


def normalized_variants(name: str) -> set[str]:
    """Create a set of normalized variants for robust comparison.

    This includes:
    - trimmed original
    - HTML-unescaped
    - HTML-escaped (to match either storage form)

    Args:
        name: The input name/identifier

    Returns:
        A set of possible normalized representations.
    """
    trimmed: str = name.strip()
    # html.unescape is idempotent on unescaped strings
    unescaped: str = html.unescape(trimmed)
    # Escape with quotes to cover common entities; escape is idempotent for already-escaped where applicable
    escaped: str = html.escape(trimmed, quote=True)
    variants: set[str] = {trimmed, unescaped, escaped}
    return {v for v in variants if v}


def already_posted(game_service: GameService, game_name: str) -> bool:
    """Check if the game has already been posted.

    Args:
        game_service (GameService): The game service to check.
        game_name (str): The name of the game to check.

    Returns:
        bool: True if already has been posted. False if not.
    """
    previous_games: Path = Path(settings.app_dir) / f"{game_service.value.lower()}.txt"
    previous_games.touch()

    try:
        with previous_games.open("r", encoding="utf-8") as file:
            target_variants: set[str] = normalized_variants(game_name)
            for line in file:
                stored_variants: set[str] = normalized_variants(line)
                if stored_variants & target_variants:
                    return True

    except OSError as e:
        logger.warning(f"Skipping '{game_name}' due to file error - treating as already posted to prevent spam.")

        e.add_note(f"Failed to read {previous_games}")
        e.add_note("Is the path correct and accessible?")
        e.add_note(f"Path is owned by: {previous_games.stat().st_uid}, check if the user running the script has access.")
        logger.error(e)

        return True

    return False


def already_posted_upcoming(game_service: GameService, game_name: str) -> bool:
    """Check if the game has already been posted as upcoming.

    Args:
        game_service (GameService): The game service to check.
        game_name (str): The name of the game to check.

    Returns:
        bool: True if already has been posted as upcoming. False if not.
    """
    previous_games: Path = Path(settings.app_dir) / f"{game_service.value.lower()}_upcoming.txt"
    previous_games.touch()

    try:
        with previous_games.open("r", encoding="utf-8") as file:
            target_variants: set[str] = normalized_variants(game_name)
            for line in file:
                stored_variants: set[str] = normalized_variants(line)
                if stored_variants & target_variants:
                    return True

    except OSError as e:
        logger.warning(f"Skipping '{game_name}' due to file error - treating as already posted to prevent spam.")

        e.add_note(f"Failed to read {previous_games}")
        e.add_note("Is the path correct and accessible?")
        e.add_note(f"Path is owned by: {previous_games.stat().st_uid}, check if the user running the script has access.")
        logger.error(e)

        return True

    return False
