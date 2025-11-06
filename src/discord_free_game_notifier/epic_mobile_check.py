from typing import TYPE_CHECKING

from discord_free_game_notifier import epic_mobile
from discord_free_game_notifier import webhook

if TYPE_CHECKING:
    from discord_webhook import DiscordEmbed


def main() -> None:
    """Check epic_mobile.json for free games and send notifications.

    This module is the notification-only counterpart to
    `discord_free_game_notifier.epic_mobile`, which now only generates
    the JSON file.
    """
    free_games: list[tuple[DiscordEmbed, str]] | None = epic_mobile.get_epic_mobile_free_games()
    if free_games:
        for embed, game_id in free_games:
            webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.EPIC)


if __name__ == "__main__":
    main()
