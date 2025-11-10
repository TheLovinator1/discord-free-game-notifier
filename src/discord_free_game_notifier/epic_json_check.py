from __future__ import annotations

from typing import TYPE_CHECKING

from discord_free_game_notifier import epic_json
from discord_free_game_notifier import webhook

if TYPE_CHECKING:
    from discord_webhook import DiscordEmbed


def main() -> None:
    """Check epic.json for free games and send notifications.

    This module is the notification-only counterpart to
    `discord_free_game_notifier.epic_json`, which now only generates
    the JSON file.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = epic_json.get_epic_json_games()
    if free_games:
        for embed, game_id in free_games:
            webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.EPIC)


if __name__ == "__main__":
    main()
