from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from typing import Any
from typing import Self

from discord_free_game_notifier import steam_json as steam_json_mod
from discord_free_game_notifier.steam_json import SteamFreeGames
from discord_free_game_notifier.steam_json import get_steam_json_games
from discord_free_game_notifier.webhook import embed_to_dict

if TYPE_CHECKING:
    from types import TracebackType

    import pytest
    from discord_webhook import DiscordEmbed


class _DummyResponse:
    def __init__(self, payload: dict[str, Any], is_error: bool = False) -> None:
        self._payload: dict[str, Any] = payload
        self.is_error: bool = is_error
        self.status_code: int = 200
        self.reason_phrase: str = "OK"

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload: dict[str, Any] = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        return None

    def get(self, url: str) -> _DummyResponse:
        assert url == "https://thelovinator1.github.io/discord-free-game-notifier/steam.json"
        return _DummyResponse(payload=self._payload)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


def test_steam_free_games_model_validate_empty_payload() -> None:
    model: SteamFreeGames = SteamFreeGames.model_validate({"free_games": []})

    assert model.free_games == []


def test_get_steam_json_games_validates_response_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    start_date: datetime.datetime = now - datetime.timedelta(hours=1)
    end_date: datetime.datetime = now + datetime.timedelta(hours=1)
    payload: dict[str, Any] = {
        "free_games": [
            {
                "id": "steam_json_test_game",
                "game_name": "Steam JSON Test Game",
                "game_url": "https://store.steampowered.com/app/123456/Steam_JSON_Test_Game/",
                "start_date": _iso(start_date),
                "end_date": _iso(end_date),
                "image_link": "https://example.com/steam-json-test-game.jpg",
                "description": "Test description",
                "developer": "Test Developer",
            },
        ],
    }

    monkeypatch.setattr(steam_json_mod.httpx, "Client", lambda timeout=30: _DummyClient(payload))  # type: ignore[assignment]

    def already_posted_stub(game_service: steam_json_mod.GameService, game_name: str) -> bool:
        assert game_service is steam_json_mod.GameService.STEAM
        assert game_name == "steam_json_test_game"
        return False

    monkeypatch.setattr(steam_json_mod, "already_posted", already_posted_stub)

    results: list[tuple[DiscordEmbed, str]] | None = get_steam_json_games()

    assert isinstance(results, list)
    assert len(results) == 1

    embed, game_id = results[0]
    assert game_id == "steam_json_test_game"

    embed_dict: dict[str, Any] = embed_to_dict(embed)
    assert embed_dict["description"] == "Test description"
    assert embed_dict["image"]["url"] == "https://example.com/steam-json-test-game.jpg"

    fields: dict[Any, Any] = {field["name"]: field["value"] for field in embed_dict.get("fields", [])}
    assert fields == {
        "Start": f"<t:{int(start_date.timestamp())}:R>",
        "End": f"<t:{int(end_date.timestamp())}:R>",
    }
