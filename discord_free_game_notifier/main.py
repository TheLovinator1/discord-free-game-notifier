from dhooks import Webhook

from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.settings import Settings
from discord_free_game_notifier.steam import get_free_steam_games

hook = Webhook(Settings.webhook_url)


def main():
    try:
        epic_embed = get_free_epic_games()
        for game in epic_embed:
            hook.send(embed=game)
        steam_embed = get_free_steam_games()
        for game in steam_embed:
            hook.send(embed=game)
    except Exception as e:
        hook.send(f"Error: {e}")
        print(e)


if __name__ == "__main__":
    main()
