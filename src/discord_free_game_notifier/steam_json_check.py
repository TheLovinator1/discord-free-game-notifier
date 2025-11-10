from __future__ import annotations

from typing import TYPE_CHECKING

from discord_free_game_notifier import steam_json
from discord_free_game_notifier import webhook

if TYPE_CHECKING:
    from discord_webhook import DiscordEmbed


def main() -> None:
    """Check steam.json for free games and send notifications.

    This module is the notification-only counterpart to
    `discord_free_game_notifier.steam_json`, which now only generates
    the JSON file.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = steam_json.get_steam_json_games()
    if free_games:
        for embed, game_id in free_games:
            webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.STEAM)


if __name__ == "__main__":
    main()
