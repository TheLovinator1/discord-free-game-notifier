"""Main file for discord_free_game_notifier.

This file contains the main function for discord_free_game_notifier.
"""
from dhooks import Webhook

from discord_free_game_notifier import settings
from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.gog import get_free_gog_games
from discord_free_game_notifier.steam import get_free_steam_games

hook = Webhook(settings.webhook_url)


def main():
    """Check for free games on Epic and Steam and send them to Discord.
    If there is an error, it will be sent to Discord.
    """
    try:
        epic_embed = get_free_epic_games()
        for game in epic_embed:
            hook.send(embed=game)
        steam_embed = get_free_steam_games()
        for game in steam_embed:
            hook.send(embed=game)
        gog_embed = get_free_gog_games()
        for game in gog_embed:
            hook.send(embed=game)
    except Exception as exception:
        hook.send(
            f"Error: {exception}\nYou should write an issue at"
            " https://github.com/TheLovinator1/discord-free-game-notifier/"
            " or contact TheLovinator#9276 if this keeps happening :-)"
        )
        print(exception)


if __name__ == "__main__":
    main()
