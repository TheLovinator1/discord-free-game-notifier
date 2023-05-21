from typing import TYPE_CHECKING

from discord_webhook import DiscordEmbed

from discord_free_game_notifier.webhook import send_embed_webhook, send_webhook

if TYPE_CHECKING:
    from requests import Response

STATUS_OK = 200


def test_send_webhook() -> None:
    """Send a normal webhook to Discord."""
    result: Response = send_webhook("Hello")
    assert result.status_code == STATUS_OK
    assert result.ok


def test_send_embed_webhook() -> None:
    """Send an embed to Discord."""
    embed = DiscordEmbed(
        title="Hello",
        description="World",
    )

    result: Response = send_embed_webhook(embed)
    assert result.status_code == STATUS_OK
    assert result.ok
