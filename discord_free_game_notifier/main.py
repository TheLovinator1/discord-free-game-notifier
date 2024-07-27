from __future__ import annotations

# app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def api():
    # İşlemlerinizi burada yapın
    return jsonify({'mesaj': 'Merhaba, Dünya!'})

if __name__ == '__main__':
    app.run(debug=True)

import datetime
from typing import TYPE_CHECKING

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from discord_free_game_notifier import settings
from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.epic_json import scrape_epic_json
from discord_free_game_notifier.gog import (
    get_free_gog_game,
    get_free_gog_game_from_store,
)
from discord_free_game_notifier.steam import get_free_steam_games
from discord_free_game_notifier.steam_json import scrape_steam_json
from discord_free_game_notifier.ubisoft import get_ubisoft_free_games
from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook

if TYPE_CHECKING:
    from discord_webhook import DiscordEmbed
    from requests import Response

sched = BlockingScheduler()


def my_listener(event: JobExecutionEvent) -> None:
    """Send a message to the webhook when a job failed."""
    if event.exception:
        logger.error("Job failed: {}", event.exception)


def send_games(game: DiscordEmbed | None, game_service: str = "Unknown") -> None:
    """Send the embed to Discord.

    Args:
        game: The embed.
        game_service: The name of the game service (Steam/GOG/Epic)
    """
    if game:
        response: Response = send_embed_webhook(game, game_service)

        if not response.ok:
            msg: str = f"Error when checking game for {game_service}:\n{response.status_code} - {response.reason}: {response.text}"
            logger.error(msg)
            send_webhook(msg)
    else:
        logger.bind(game_name=f"{game_service}").info("No free games found")


def check_free_games() -> None:  # noqa: C901, PLR0912
    """Check for free games on Epic, Steam, GOG and Ubisoft and send them to Discord."""
    logger.info("Checking for free games")

    try:
        for game in get_free_epic_games():
            send_games(game, "Epic")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking Epic for free games: {e}"
        logger.error(msg)

    try:
        for game in get_free_steam_games():
            send_games(game, "Steam")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking Steam for free games: {e}"
        logger.error(msg)

    try:
        for game in get_free_gog_game_from_store():
            send_games(game, "GOG")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking GOG (search page) for free games: {e}"
        logger.error(msg)

    try:
        if gog_embed := get_free_gog_game():
            send_games(gog_embed, "GOG")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking GOG (front page) free games: {e}"
        logger.error(msg)

    try:
        for game in get_ubisoft_free_games():
            send_games(game, "Ubisoft")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking Ubisoft for free games: {e}"
        logger.error(msg)

    try:
        for game in scrape_epic_json():
            send_games(game, "Epic")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking Epic (JSON) for free games: {e}"
        logger.error(msg)

    try:
        for game in scrape_steam_json():
            send_games(game, "Steam")
    except Exception as e:  # noqa: BLE001
        msg: str = f"Error when checking Steam (JSON) for free games: {e}"
        logger.error(msg)


def main() -> None:
    """Main function for discord_free_game_notifier.

    This function will check for free games every 15 minutes.
    """
    logger.info(
        "Starting discord_free_game_notifier, checking for free games every 15 minutes",
    )
    sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info("Adding job to scheduler")
    sched.add_job(
        check_free_games,
        "cron",
        minute="*/15",
        replace_existing=True,
        next_run_time=datetime.datetime.now(tz=datetime.UTC),
    )
    logger.info("Starting scheduler")
    sched.start()


if __name__ == "__main__":
    if settings.webhook_url == settings.default_webhook_url:
        logger.error(
            "Webhook URL is the default value. Please modify it in the .env file.",
        )

    main()
