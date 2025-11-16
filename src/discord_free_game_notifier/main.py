from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from typing import Any

import httpx
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.events import JobExecutionEvent
from apscheduler.schedulers.blocking import BlockingScheduler
from discord_webhook import DiscordEmbed
from loguru import logger

from discord_free_game_notifier import settings
from discord_free_game_notifier.epic import get_free_epic_games
from discord_free_game_notifier.epic_json import get_epic_json_games
from discord_free_game_notifier.epic_mobile import get_epic_mobile_json_games
from discord_free_game_notifier.gog import get_free_gog_game
from discord_free_game_notifier.gog import get_free_gog_game_from_store
from discord_free_game_notifier.steam import get_free_steam_games
from discord_free_game_notifier.steam_json import get_steam_json_games
from discord_free_game_notifier.ubisoft import get_ubisoft_free_games
from discord_free_game_notifier.webhook import GameService
from discord_free_game_notifier.webhook import send_embed_webhook
from discord_free_game_notifier.webhook import send_text_webhook

if TYPE_CHECKING:
    from collections.abc import Callable

sched = BlockingScheduler()


def my_listener(event: JobExecutionEvent) -> None:
    """Send a message to the webhook when a job failed."""
    if event.exception:
        logger.error("Job failed: {}", event.exception)


def _safe_check_service(service_name: str, check_function: Callable[[], Any]) -> None:
    """Safely execute a game service check function with error handling.

    Args:
        service_name: Human-readable name of the service being checked.
        check_function: Function to call that checks for free games.
    """
    try:
        check_function()
    except (httpx.HTTPError, LookupError, ValueError, AttributeError, TypeError, OSError) as e:
        logger.exception(f"Error when checking {service_name} for free games: {e}")


def _check_epic_games() -> None:
    """Check Epic Games (API) for free games."""
    epic_games: list[tuple[DiscordEmbed | str, str, bool]] | None = get_free_epic_games()
    if not epic_games:
        return

    for content, game_id, is_upcoming in epic_games:
        if is_upcoming and isinstance(content, str):
            send_text_webhook(message=content, game_id=game_id, game_service=GameService.EPIC)
        elif isinstance(content, DiscordEmbed):
            send_embed_webhook(embed=content, game_id=game_id, game_service=GameService.EPIC)


def _check_epic_json_games() -> None:
    """Check Epic Games (JSON) for free games."""
    epic_json_games: list[tuple[DiscordEmbed, str]] | None = get_epic_json_games()
    if epic_json_games:
        for embed, game_id in epic_json_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.EPIC)


def _check_epic_mobile_json_games() -> None:
    """Check Epic Games Mobile (JSON) for free games."""
    epic_mobile_json_games: list[tuple[DiscordEmbed, str]] | None = get_epic_mobile_json_games()
    if epic_mobile_json_games:
        for embed, game_id in epic_mobile_json_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.EPIC)


def _check_steam_games() -> None:
    """Check Steam for free games."""
    steam_games: list[tuple[DiscordEmbed, str]] | None = get_free_steam_games()
    if steam_games:
        for embed, game_id in steam_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.STEAM)


def _check_steam_json_games() -> None:
    """Check Steam (JSON) for free games."""
    steam_json_games: list[tuple[DiscordEmbed, str]] | None = get_steam_json_games()
    if steam_json_games:
        for embed, game_id in steam_json_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.STEAM)


def _check_gog_store_games() -> None:
    """Check GOG store search for free games."""
    gog_store_games: list[tuple[DiscordEmbed, str]] = get_free_gog_game_from_store()
    if gog_store_games:
        for embed, game_id in gog_store_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.GOG)


def _check_gog_front_page() -> None:
    """Check GOG front page for free games."""
    gog_game: tuple[DiscordEmbed, str] | None = get_free_gog_game()
    if gog_game:
        embed, game_id = gog_game
        send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.GOG)


def _check_ubisoft_games() -> None:
    """Check Ubisoft for free games."""
    ubisoft_games: list[tuple[DiscordEmbed, str]] | None = get_ubisoft_free_games()
    if ubisoft_games:
        for embed, game_id in ubisoft_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.UBISOFT)


def check_free_games() -> None:
    """Check for free games on Epic, Steam, GOG and Ubisoft and send them to Discord."""
    logger.info("Checking for free games")

    # Check Epic Games if enabled and PC or mobile platforms are enabled
    if settings.is_store_enabled("epic"):
        if settings.is_platform_enabled("pc"):
            _safe_check_service("Epic (API)", _check_epic_games)
            _safe_check_service("Epic (JSON)", _check_epic_json_games)
        if settings.is_platform_enabled("android") or settings.is_platform_enabled("ios"):
            _safe_check_service("Epic (Mobile JSON)", _check_epic_mobile_json_games)

    # Check Steam if enabled and PC platform is enabled
    if settings.is_store_enabled("steam") and settings.is_platform_enabled("pc"):
        _safe_check_service("Steam", _check_steam_games)
        _safe_check_service("Steam (JSON)", _check_steam_json_games)

    # Check GOG if enabled and PC platform is enabled
    if settings.is_store_enabled("gog") and settings.is_platform_enabled("pc"):
        _safe_check_service("GOG (store search)", _check_gog_store_games)
        _safe_check_service("GOG (front page)", _check_gog_front_page)

    # Check Ubisoft if enabled and PC platform is enabled
    if settings.is_store_enabled("ubisoft") and settings.is_platform_enabled("pc"):
        _safe_check_service("Ubisoft", _check_ubisoft_games)


def main() -> None:
    """Main function for discord_free_game_notifier.

    This function will check for free games at minute 01, 16, 31, and 46 of each hour.
    """
    logger.info("Starting discord_free_game_notifier, checks scheduled at xx:01, xx:16, xx:31, xx:46 each hour")
    sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info("Adding job to scheduler")
    sched.add_job(check_free_games, "cron", minute="1,16,31,46", next_run_time=datetime.datetime.now(tz=datetime.UTC))
    logger.info("Starting scheduler")
    try:
        sched.start()
    except KeyboardInterrupt, SystemExit:
        logger.info("Shutting down gracefully, waiting for current jobs to finish...")
        sched.shutdown(wait=True)
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
