from __future__ import annotations

from typing import Any

from discord_webhook import DiscordEmbed

from discord_free_game_notifier.webhook import embed_to_dict


class TestEmbedToDict:
    def test_embed_to_dict_with_all_attributes(self) -> None:
        """Test embed_to_dict with all attributes set."""
        embed = DiscordEmbed(
            title="Test Title",
            description="Test Description",
            url="https://example.com",
            color=123456,
            timestamp="2023-01-01T00:00:00.000Z",
            footer={"text": "Footer Text"},
            image={"url": "https://example.com/image.png"},
            thumbnail={"url": "https://example.com/thumb.png"},
            author={"name": "Author Name"},
            provider={"name": "Provider Name"},
            video={"url": "https://example.com/video.mp4"},
            fields=[{"name": "Field1", "value": "Value1"}],
        )
        result: dict[str, Any] = embed_to_dict(embed)
        expected: dict[str, str | int | dict[str, str] | list[dict[str, str]]] = {
            "title": "Test Title",
            "description": "Test Description",
            "url": "https://example.com",
            "color": 123456,
            "timestamp": "2023-01-01T00:00:00.000Z",
            "footer": {"text": "Footer Text"},
            "image": {"url": "https://example.com/image.png"},
            "thumbnail": {"url": "https://example.com/thumb.png"},
            "author": {"name": "Author Name"},
            "provider": {"name": "Provider Name"},
            "video": {"url": "https://example.com/video.mp4"},
            "fields": [{"name": "Field1", "value": "Value1"}],
        }
        assert result == expected, f"Expected {expected} but got {result}"

    def test_embed_to_dict_with_none_attributes(self) -> None:
        """Test embed_to_dict with some attributes None."""
        embed = DiscordEmbed(title="Test Title")
        result: dict[str, Any] = embed_to_dict(embed)
        expected: dict[str, str | list[Any] | None] = {
            "title": "Test Title",
            "description": None,
            "url": None,
            "color": None,
            "timestamp": None,
            "footer": None,
            "image": None,
            "thumbnail": None,
            "author": None,
            "provider": None,
            "video": None,
            "fields": [],
        }
        assert result == expected, f"Expected {expected} but got {result}"

    def test_embed_to_dict_empty_embed(self) -> None:
        """Test embed_to_dict with an empty embed."""
        embed = DiscordEmbed()
        result: dict[str, Any] = embed_to_dict(embed)
        expected: dict[str, list[Any] | None] = {
            "title": None,
            "description": None,
            "url": None,
            "color": None,
            "timestamp": None,
            "footer": None,
            "image": None,
            "thumbnail": None,
            "author": None,
            "provider": None,
            "video": None,
            "fields": [],
        }
        assert result == expected, f"Expected {expected} but got {result}"
