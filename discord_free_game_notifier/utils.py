from __future__ import annotations

from pathlib import Path


def already_posted(previous_games: Path, game_name: str) -> bool:
    """Check if the game has already been posted.

    Args:
        previous_games: The file where we store old games in.
        game_name: The game name, we check if this is in the file.

    Returns:
        bool: True if already has been posted.
    """
    previous_games = Path(previous_games)

    if Path.is_file(previous_games):
        with Path.open(previous_games, "r", encoding="utf-8") as file:
            if game_name in file.read():
                return True
    return False
