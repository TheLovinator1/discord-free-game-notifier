from __future__ import annotations

import enum
import html
import pathlib
import textwrap
from typing import TYPE_CHECKING
from typing import Any

from discord_webhook import DiscordEmbed
from discord_webhook import DiscordWebhook
from loguru import logger

from discord_free_game_notifier import settings

if TYPE_CHECKING:
    import requests


class GameService(enum.StrEnum):
    """Current supported game services.

    We have support for sending to different webhooks based on the game service.
    """

    STEAM = "Steam"
    """Send embed to Steam webhook URL. Uses the STEAM_WEBHOOK environment variable."""

    GOG = "GOG"
    """Send embed to GOG webhook URL. Uses the GOG_WEBHOOK environment variable."""

    EPIC = "Epic"
    """Send embed to Epic webhook URL. Uses the EPIC_WEBHOOK environment variable."""

    UBISOFT = "Ubisoft"
    """Send embed to Ubisoft webhook URL. Uses the UBISOFT_WEBHOOK environment variable."""


def get_webhook_url(game_service: GameService) -> str:
    """Get the appropriate webhook URL for a game service.

    Args:
        game_service: The game service to get webhook for.

    Returns:
        str: The webhook URL to use.
    """
    webhook_url: str = settings.webhook_url
    if game_service is GameService.EPIC and settings.epic_webhook:
        logger.debug(f"Using {game_service.name} webhook: {settings.epic_webhook}")
        webhook_url = settings.epic_webhook
    elif game_service is GameService.GOG and settings.gog_webhook:
        logger.debug(f"Using {game_service.name} webhook: {settings.gog_webhook}")
        webhook_url = settings.gog_webhook
    elif game_service is GameService.STEAM and settings.steam_webhook:
        logger.debug(f"Using {game_service.name} webhook: {settings.steam_webhook}")
        webhook_url = settings.steam_webhook
    elif game_service is GameService.UBISOFT and settings.ubisoft_webhook:
        logger.debug(f"Using {game_service.name} webhook: {settings.ubisoft_webhook}")
        webhook_url = settings.ubisoft_webhook
    else:
        logger.debug(f"Using main webhook: {webhook_url}")
    return webhook_url


def embed_to_dict(embed: DiscordEmbed) -> dict[str, Any]:
    """Convert a DiscordEmbed to a dictionary.

    Args:
        embed (DiscordEmbed): The embed to convert.

    Returns:
        dict: The embed as a dictionary.
    """
    return {
        "title": getattr(embed, "title", None),
        "description": getattr(embed, "description", None),
        "url": getattr(embed, "url", None),
        "color": getattr(embed, "color", None),
        "timestamp": getattr(embed, "timestamp", None),
        "footer": getattr(embed, "footer", None),
        "image": getattr(embed, "image", None),
        "thumbnail": getattr(embed, "thumbnail", None),
        "author": getattr(embed, "author", None),
        "provider": getattr(embed, "provider", None),
        "video": getattr(embed, "video", None),
        "fields": getattr(embed, "fields", None),
    }


def send_embed_webhook(embed: DiscordEmbed, game_id: str, game_service: GameService) -> None:
    """Send an embed to Discord.

    Args:
        embed (DiscordEmbed): Embed to send to Discord.
        game_id (str): The ID of the game. Used for for adding to the posted games list.
        game_service (GameService): The name of the game service (Steam/GOG/Epic)
    """
    webhook_url: str = get_webhook_url(game_service)
    webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)
    webhook.add_embed(embed=embed)

    embed.description = textwrap.shorten(embed.description or "", width=1000, placeholder="...")

    response: requests.Response = webhook.execute()

    if response.ok:
        logger.info(f"Sent embed for {game_id=} to {game_service=}")
        # Persist a trimmed, unescaped identifier to avoid duplicates caused by formatting
        normalized_id: str = html.unescape(str(game_id)).strip()
        with pathlib.Path(f"{settings.app_dir}/{game_service.lower()}.txt").open(mode="a+", encoding="utf-8") as file:
            file.write(f"{normalized_id}\n")
    else:
        logger.error(f"Failed to send embed for {game_id=} to {game_service=}: {response.status_code} - {response.text}")
        logger.error(f"Response content: {response.text}")
        logger.error(f"Embed content: {embed_to_dict(embed)}")


def send_text_webhook(message: str, game_id: str, game_service: GameService) -> None:
    """Send a plain text message to Discord for upcoming games.

    Args:
        message (str): The text message to send to Discord.
        game_id (str): The ID of the game. Used for adding to the upcoming games list.
        game_service (GameService): The name of the game service (Steam/GOG/Epic)
    """
    webhook_url: str = get_webhook_url(game_service)
    webhook = DiscordWebhook(url=webhook_url, content=message, rate_limit_retry=True)

    response: requests.Response = webhook.execute()

    if response.ok:
        logger.info(f"Sent text message for {game_id=} to {game_service=}")
        # Persist a trimmed, unescaped identifier to avoid duplicates caused by formatting
        normalized_id: str = html.unescape(str(game_id)).strip()
        with pathlib.Path(f"{settings.app_dir}/{game_service.lower()}_upcoming.txt").open(mode="a+", encoding="utf-8") as file:
            file.write(f"{normalized_id}\n")
    else:
        logger.error(f"Failed to send text message for {game_id=} to {game_service=}: {response.status_code} - {response.text}")
        logger.error(f"Response content: {response.text}")
