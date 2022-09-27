from discord_webhook import DiscordEmbed

from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook


def test_send_webhook():
    """
    Send a normal webhook to Discord.
    """
    result = send_webhook("Hello")
    assert result.status_code == 200
    assert result.ok


def test_send_embed_webhook():
    """
    Send an embed to Discord.
    """
    embed = DiscordEmbed(
        title="Hello",
        description="World",
    )

    result = send_embed_webhook(embed)
    assert result.status_code == 200
    assert result.ok
