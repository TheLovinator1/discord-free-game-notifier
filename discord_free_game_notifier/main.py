"""Main file for discord_free_game_notifier.

This file contains the main function for discord_free_game_notifier.
"""

import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler

from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.gog import get_free_gog_game
from discord_free_game_notifier.steam import get_free_steam_games
from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook

sched = BlockingScheduler()


def my_listener(event):
    """Send a message to the webhook when a job failed."""
    if event.exception:
        send_webhook(f"Job failed: {event.exception}")


def send_games(game, game_service="Unknown"):
    response = send_embed_webhook(game)

    if not response.ok:
        send_webhook(
            f"Error when checking game for {game_service}:\n{response.status_code} - {response.reason}: {response.text}")


def check_free_games():
    """Check for free games on Epic, Steam and GOG and send them to
    Discord."""
    # Check for free games on Epic
    epic_embed = get_free_epic_games()
    for game in epic_embed:
        send_games(game, "Epic")

    # Check for free games on Steam
    steam_embed = get_free_steam_games()
    for game in steam_embed:
        send_games(game, "Steam")

    # Check for free games on GOG
    gog_embed = get_free_gog_game()
    if gog_embed:
        send_games(gog_embed, "GOG")


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
