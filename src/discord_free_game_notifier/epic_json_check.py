from discord_free_game_notifier import epic_json
from discord_free_game_notifier import webhook


def main() -> None:
    """Check epic.json for free games and send notifications.

    This module is the notification-only counterpart to
    `discord_free_game_notifier.epic_json`, which now only generates
    the JSON file.
    """
    free_games = epic_json.get_epic_free_games()
    if free_games:
        for embed, game_id in free_games:
            webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.EPIC)


if __name__ == "__main__":
    main()
