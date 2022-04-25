from discord_webhook import DiscordEmbed, DiscordWebhook

from discord_free_game_notifier import settings


def send_webhook(message: str) -> None:
    """Send a message to Discord.

    Args:
        message (str): Message to send to Discord.
    """
    webhook = DiscordWebhook(url=settings.webhook_url, content=message)
    response = webhook.execute()
    settings.logger.debug(f"Webhook - Response: {response}")


def send_embed_webhook(embed: DiscordEmbed) -> None:
    """Send an embed to Discord.

    Args:
        embed (DiscordEmbed): Embed to send to Discord.
    """
    webhook = DiscordWebhook(url=settings.webhook_url)

    # Add embed object to webhook
    webhook.add_embed(embed)

    response = webhook.execute()
    settings.logger.debug(f"Webhook, Embed - Response: {response}")
