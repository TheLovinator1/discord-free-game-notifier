from pathlib import Path

from discord_free_game_notifier import settings


def already_posted(previous_games: Path, game_name: str) -> bool:
    """Check if the game has already been posted.

    Args:
        previous_games: The file where we store old games in.
        game_name: The game name, we check if this is in the file.

    Returns:
        bool: True if already has been posted.
    """
    if Path.is_file(Path(previous_games)):
        with Path.open(Path(previous_games), "r", encoding="utf-8") as file:
            if game_name in file.read():
                settings.logger.debug("\tHas already been posted before. Skipping!")
                return True
    return False
