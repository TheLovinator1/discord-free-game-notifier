from discord_free_game_notifier import steam_json
from discord_free_game_notifier import webhook


def main() -> None:
    """Check steam.json for free games and send notifications.

    This module is the notification-only counterpart to
    `discord_free_game_notifier.steam_json`, which now only generates
    the JSON file.
    """
    free_games = steam_json.get_steam_free_games()
    if free_games:
        for embed, game_id in free_games:
            webhook.send_embed_webhook(embed=embed, game_id=game_id, game_service=webhook.GameService.STEAM)


if __name__ == "__main__":
    main()
