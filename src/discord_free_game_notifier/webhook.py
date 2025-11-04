import enum
import html
import pathlib
import textwrap
from typing import TYPE_CHECKING
from typing import Any

import requests
from discord_webhook import DiscordEmbed
from discord_webhook import DiscordWebhook
from loguru import logger
from requests.models import Response

from discord_free_game_notifier import settings

if TYPE_CHECKING:
    from requests import Response


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
    webhook_url: str = settings.webhook_url
    if game_service is GameService.EPIC and settings.epic_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.epic_webhook
    elif game_service is GameService.GOG and settings.gog_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.gog_webhook
    elif game_service is GameService.STEAM and settings.steam_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.steam_webhook
    elif game_service is GameService.UBISOFT and settings.ubisoft_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.ubisoft_webhook

    webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)
    webhook.add_embed(embed=embed)

    embed.description = textwrap.shorten(embed.description or "", width=1000, placeholder="...")

    try:
        response: Response = webhook.execute()

        if response.ok:
            logger.info(f"Sent embed for {game_id=} to {game_service=}")
            # Persist a trimmed, unescaped identifier to avoid duplicates caused by formatting
            normalized_id: str = html.unescape(str(game_id)).strip()
            with pathlib.Path(f"{settings.app_dir}/{game_service.lower()}.txt").open(mode="a+", encoding="utf-8") as file:
                file.write(f"{normalized_id}\n")
        else:
            logger.error(f"Failed to send embed for {game_id=} to {game_service=}: {response.status_code} - {response.text}")
            logger.error(f"Response content: {response.content}")
            logger.error(f"Embed content: {embed_to_dict(embed)}")
    except (requests.RequestException, requests.HTTPError, requests.ConnectionError, requests.Timeout, OSError) as e:
        logger.error(f"Exception when sending embed for {game_id=} to {game_service=}: {e}")


def send_text_webhook(message: str, game_id: str, game_service: GameService) -> None:
    """Send a plain text message to Discord for upcoming games.

    Args:
        message (str): The text message to send to Discord.
        game_id (str): The ID of the game. Used for adding to the upcoming games list.
        game_service (GameService): The name of the game service (Steam/GOG/Epic)
    """
    webhook_url: str = settings.webhook_url
    if game_service is GameService.EPIC and settings.epic_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.epic_webhook
    elif game_service is GameService.GOG and settings.gog_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.gog_webhook
    elif game_service is GameService.STEAM and settings.steam_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.steam_webhook
    elif game_service is GameService.UBISOFT and settings.ubisoft_webhook:
        logger.info(f"Using {game_service.name} webhook")
        webhook_url = settings.ubisoft_webhook

    webhook = DiscordWebhook(url=webhook_url, content=message, rate_limit_retry=True)

    try:
        response: Response = webhook.execute()

        if response.ok:
            logger.info(f"Sent text message for {game_id=} to {game_service=}")
            # Persist a trimmed, unescaped identifier to avoid duplicates caused by formatting
            normalized_id: str = html.unescape(str(game_id)).strip()
            with pathlib.Path(f"{settings.app_dir}/{game_service.lower()}_upcoming.txt").open(mode="a+", encoding="utf-8") as file:
                file.write(f"{normalized_id}\n")
        else:
            logger.error(f"Failed to send text message for {game_id=} to {game_service=}: {response.status_code} - {response.text}")
            logger.error(f"Response content: {response.content}")
    except (requests.RequestException, requests.HTTPError, requests.ConnectionError, requests.Timeout, OSError) as e:
        logger.error(f"Exception when sending text message for {game_id=} to {game_service=}: {e}")
