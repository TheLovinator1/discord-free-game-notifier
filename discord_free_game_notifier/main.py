"""Main file for discord_free_game_notifier.

This file contains the main function for discord_free_game_notifier.
"""

import datetime
from typing import TYPE_CHECKING

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.blocking import BlockingScheduler
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings
from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.gog import get_free_gog_game
from discord_free_game_notifier.steam import get_free_steam_games
from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook

if TYPE_CHECKING:
    from requests import Response

sched = BlockingScheduler()


def my_listener(event: JobExecutionEvent) -> None:
    """Send a message to the webhook when a job failed."""
    if event.exception:
        send_webhook(f"Job failed: {event.exception}")


def send_games(game: DiscordEmbed | None, game_service: str = "Unknown") -> None:
    """Send the embed to Discord.

    Args:
        game: The embed.
        game_service: The name of the game service (Steam/GOG/Epic)
    """
    if game:
        response: Response = send_embed_webhook(game, game_service)

        if not response.ok:
            send_webhook(
                (
                    f"Error when checking game for {game_service}:\n"
                    f"{response.status_code} - {response.reason}: {response.text}"
                ),
            )
    else:
        settings.logger.info("No free games found for {}", game_service)


def check_free_games() -> None:
    """Check for free games on Epic, Steam and GOG and send them to Discord."""
    for game in get_free_epic_games():
        send_games(game, "Epic")

    for game in get_free_steam_games():
        send_games(game, "Steam")

    if gog_embed := get_free_gog_game():
        send_games(gog_embed, "GOG")


def main() -> None:
    """Main function for discord_free_game_notifier.

    This function will check for free games every 30 minutes.
    """
    sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    sched.add_job(
        check_free_games,
        "cron",
        minute="*/15",
        replace_existing=True,
        next_run_time=datetime.datetime.now(tz=datetime.UTC),
    )
    sched.start()


if __name__ == "__main__":
    main()
