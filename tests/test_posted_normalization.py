from typing import TYPE_CHECKING

import pytest
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings as settings_mod
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.utils import already_posted_upcoming
from discord_free_game_notifier.webhook import GameService
from discord_free_game_notifier.webhook import send_embed_webhook
from discord_free_game_notifier.webhook import send_text_webhook

if TYPE_CHECKING:
    from pathlib import Path


class _DummyResponse:
    def __init__(self, ok: bool = True) -> None:  # noqa: FBT001, FBT002
        self.ok: bool = ok
        self.status_code = 200
        self.text = "OK"
        self.content = b"OK"


class _DummyWebhook:
    def __init__(self, url: str, content: str | None = None, rate_limit_retry: bool = False) -> None:  # noqa: FBT001, FBT002
        self.url: str = url
        self.content: str | None = content
        self.rate_limit_retry: bool = rate_limit_retry
        self._embeds: list[DiscordEmbed] = []

    def add_embed(self, embed: DiscordEmbed) -> None:
        self._embeds.append(embed)

    def execute(self) -> _DummyResponse:
        return _DummyResponse(ok=True)


@pytest.fixture
def tmp_app_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Redirect app_dir to a temporary folder for file operations
    monkeypatch.setattr(settings_mod, "app_dir", str(tmp_path), raising=True)
    # Ensure a valid webhook URL to satisfy validation in send functions
    monkeypatch.setattr(settings_mod, "webhook_url", "https://discord.com/api/webhooks/123/test", raising=True)
    return tmp_path


def test_already_posted_trims_and_handles_html_entities(tmp_app_dir: Path) -> None:
    service = GameService.STEAM
    posted_file = tmp_app_dir / f"{service.value.lower()}.txt"
    posted_file.write_text(" Half\nTom &amp; Jerry\n", encoding="utf-8")

    assert already_posted(service, "Half") is True
    assert already_posted(service, "Tom & Jerry") is True
    assert already_posted(service, "Not In List") is False


def test_already_posted_upcoming_trims_and_handles_html_entities(tmp_app_dir: Path) -> None:
    service = GameService.STEAM
    upcoming_file = tmp_app_dir / f"{service.value.lower()}_upcoming.txt"
    upcoming_file.write_text("  Soon ™  \nFish &amp; Chips\n", encoding="utf-8")

    assert already_posted_upcoming(service, "Soon ™") is True
    assert already_posted_upcoming(service, "Fish & Chips") is True
    assert already_posted_upcoming(service, "Something Else") is False


def test_send_embed_webhook_writes_trimmed_unescaped_id(tmp_app_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock DiscordWebhook to avoid network and to trigger ok response
    monkeypatch.setattr(
        "discord_free_game_notifier.webhook.DiscordWebhook",
        _DummyWebhook,
        raising=True,
    )

    service = GameService.STEAM
    embed = DiscordEmbed(description="x")

    send_embed_webhook(embed=embed, game_id="   Tom &amp; Jerry   ", game_service=service)

    # Verify file written with trimmed, unescaped name
    posted_file: Path = tmp_app_dir / f"{service.value.lower()}.txt"
    contents: list[str] = posted_file.read_text(encoding="utf-8").splitlines()
    assert contents == ["Tom & Jerry"]


def test_send_text_webhook_writes_trimmed_unescaped_id(tmp_app_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock DiscordWebhook to avoid network and to trigger ok response
    monkeypatch.setattr(
        "discord_free_game_notifier.webhook.DiscordWebhook",
        _DummyWebhook,
        raising=True,
    )

    service = GameService.STEAM

    send_text_webhook(message="upcoming", game_id="  Fish &amp; Chips  ", game_service=service)

    # Verify file written with trimmed, unescaped name
    upcoming_file: Path = tmp_app_dir / f"{service.value.lower()}_upcoming.txt"
    contents: list[str] = upcoming_file.read_text(encoding="utf-8").splitlines()
    assert contents == ["Fish & Chips"]
