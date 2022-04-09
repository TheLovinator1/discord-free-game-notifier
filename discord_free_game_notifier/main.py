"""Main file for discord_free_game_notifier.

This file contains the main function for discord_free_game_notifier.
"""

import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from dhooks import Webhook

from discord_free_game_notifier import settings
from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.gog import get_free_gog_games
from discord_free_game_notifier.steam import get_free_steam_games

hook = Webhook(settings.webhook_url)
sched = BlockingScheduler()


def my_listener(event):
    """Send a message to the webhook when a job failed."""
    if event.exception:
        hook.send(f"Job failed: {event.exception}")


def check_free_games():
    """Check for free games on Epic and Steam and send them to Discord."""
    epic_embed = get_free_epic_games()
    for game in epic_embed:
        hook.send(embed=game)
    steam_embed = get_free_steam_games()
    for game in steam_embed:
        hook.send(embed=game)
    gog_embed = get_free_gog_games()
    for game in gog_embed:
        hook.send(embed=game)


def main():
    """Main function for discord_free_game_notifier.

    This function will check for free games every 30 minutes.
    """

    sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    sched.add_job(
        check_free_games,
        "cron",
        minute="*/30",
        replace_existing=True,
        next_run_time=datetime.datetime.now(),
    )
    sched.start()


if __name__ == "__main__":
    main()
