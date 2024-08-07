from discord_webhook import DiscordEmbed, DiscordWebhook
from loguru import logger
from requests import Response

from discord_free_game_notifier import settings


def send_webhook(message: str, game_service: str = "") -> Response:
    """Send a message to Discord.

    Args:
        message (str): Message to send to Discord.
        game_service (str): The name of the game service (Steam/GOG/Epic)

    Returns:
        Response: The response from the webhook request.
    """
    if get_webhook_url(game_service):
        webhook = DiscordWebhook(
            url=get_webhook_url(game_service),
            content=message,
            rate_limit_retry=True,
        )
        return webhook.execute()

    webhook = DiscordWebhook(
        url=settings.webhook_url,
        content=message,
        rate_limit_retry=True,
    )
    logger.debug(
        f"Sending webhook: {message} to {settings.webhook_url}\n Message: {message}\n Game service: {game_service}",
    )

    return webhook.execute()


def get_webhook_url(game_service: str) -> str:
    """Get the webhook URL for a specific game service.

    Args:
        game_service (str): The name of the game service (Steam/GOG/Epic)

    Returns:
        str: The webhook URL for the game service.
    """
    if game_service == "Epic" and settings.epic_webhook:
        logger.info("Using Epic webhook")
        return settings.epic_webhook
    if game_service == "GOG" and settings.gog_webhook:
        logger.info("Using GOG webhook")
        return settings.gog_webhook
    if game_service == "Steam" and settings.steam_webhook:
        logger.info("Using Steam webhook")
        return settings.steam_webhook

    return ""


def send_embed_webhook(embed: DiscordEmbed, game_service: str = "") -> Response:
    """Send an embed to Discord.

    Args:
        embed (DiscordEmbed): Embed to send to Discord.
        game_service (str): The name of the game service (Steam/GOG/Epic)

    Returns:
        Response: The response from the
    """
    if get_webhook_url(game_service):
        webhook = DiscordWebhook(
            url=get_webhook_url(game_service),
            rate_limit_retry=True,
        )
        webhook.add_embed(embed)
        return webhook.execute()

    webhook = DiscordWebhook(url=settings.webhook_url, rate_limit_retry=True)

    webhook.add_embed(embed)

    return webhook.execute()
