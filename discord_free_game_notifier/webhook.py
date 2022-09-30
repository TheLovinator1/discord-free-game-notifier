from discord_webhook import DiscordEmbed, DiscordWebhook

from discord_free_game_notifier import settings


def send_webhook(message: str):
    """Send a message to Discord.

    Args:
        message (str): Message to send to Discord.
    """
    webhook = DiscordWebhook(url=settings.webhook_url, content=message, rate_limit_retry=True)

    return webhook.execute()


def send_embed_webhook(embed: DiscordEmbed):
    """Send an embed to Discord.

    Args:
        embed (DiscordEmbed): Embed to send to Discord.
    """
    webhook = DiscordWebhook(url=settings.webhook_url, rate_limit_retry=True)

    # Add embed object to webhook
    webhook.add_embed(embed)

    return webhook.execute()
