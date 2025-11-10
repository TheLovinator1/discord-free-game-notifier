from __future__ import annotations

import datetime
import json
import re
from typing import TYPE_CHECKING
from typing import Any
from typing import Self

import pytest
from discord_webhook import DiscordEmbed
from pydantic import HttpUrl

from discord_free_game_notifier import epic_json as epic_mod
from discord_free_game_notifier.epic_json import EpicFreeGames
from discord_free_game_notifier.epic_json import EpicGame
from discord_free_game_notifier.epic_json import create_json_file
from discord_free_game_notifier.epic_json import get_epic_json_games
from discord_free_game_notifier.webhook import embed_to_dict

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import TracebackType


def _make_game(game_id: str) -> EpicGame:
    """Helper to create a minimal valid EpicGame.

    Args:
        game_id: The ID to assign to the EpicGame.

    Returns:
        An EpicGame instance with the specified ID.
    """
    return EpicGame(
        id=game_id,
        game_name="Test Game",
        game_url=HttpUrl("https://example.com"),
        start_date=datetime.datetime(2023, 11, 27, 13, 0, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2023, 12, 27, 13, 0, 0, tzinfo=datetime.UTC),
        image_link=HttpUrl("https://example.com/image.jpg"),
        description="Test description",
        developer="Test Developer",
    )


class TestValidateTimezoneAware:
    """Tests for the validate_timezone_aware field validator."""

    def test_valid_timezone_aware_datetime(self) -> None:
        """Test that a timezone-aware datetime passes validation."""
        dt = datetime.datetime(2023, 12, 1, 11, 0, 0, tzinfo=datetime.UTC)
        result = EpicGame.validate_timezone_aware(dt)
        assert result == dt

    def test_naive_datetime_raises_value_error(self) -> None:
        """Test that a naive datetime raises ValueError."""
        dt = datetime.datetime(2023, 12, 1, 11, 0, 0)  # noqa: DTZ001
        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            EpicGame.validate_timezone_aware(dt)

    def test_datetime_with_none_tzinfo_raises_value_error(self) -> None:
        """Test that a datetime with tzinfo=None raises ValueError."""
        dt = datetime.datetime(2023, 12, 1, 11, 0, 0, tzinfo=None)  # noqa: DTZ001
        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            EpicGame.validate_timezone_aware(dt)


class TestSerializeDatetime:
    """Tests for the serialize_datetime field serializer."""

    def test_serialize_utc_datetime_with_plus_format(self) -> None:
        """Test that UTC datetime is serialized with +00:00 format."""
        game = EpicGame(
            id="test_game",
            game_name="Test Game",
            game_url=HttpUrl("https://example.com"),
            start_date=datetime.datetime(2023, 11, 27, 13, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2023, 12, 27, 13, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/image.jpg"),
            description="Test description",
            developer="Test Developer",
        )

        serialized: dict[str, Any] = game.model_dump(mode="json")
        assert serialized["start_date"] == "2023-11-27T13:00:00+00:00"
        assert serialized["end_date"] == "2023-12-27T13:00:00+00:00"

    def test_serialize_datetime_with_different_timezone(self) -> None:
        """Test that datetime with non-UTC timezone is properly serialized."""
        tz = datetime.timezone(datetime.timedelta(hours=5))
        game = EpicGame(
            id="test_game",
            game_name="Test Game",
            game_url=HttpUrl("https://example.com"),
            start_date=datetime.datetime(2023, 11, 27, 13, 0, 0, tzinfo=tz),
            end_date=datetime.datetime(2023, 12, 27, 13, 0, 0, tzinfo=tz),
            image_link=HttpUrl("https://example.com/image.jpg"),
            description="Test description",
            developer="Test Developer",
        )

        serialized: dict[str, Any] = game.model_dump(mode="json")
        assert serialized["start_date"] == "2023-11-27T13:00:00+05:00"
        assert serialized["end_date"] == "2023-12-27T13:00:00+05:00"

    def test_serialize_datetime_preserves_microseconds(self) -> None:
        """Test that datetime serialization preserves microseconds."""
        game = EpicGame(
            id="test_game",
            game_name="Test Game",
            game_url=HttpUrl("https://example.com"),
            start_date=datetime.datetime(2023, 11, 27, 13, 0, 0, 123456, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2023, 12, 27, 13, 0, 0, 654321, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/image.jpg"),
            description="Test description",
            developer="Test Developer",
        )

        serialized: dict[str, Any] = game.model_dump(mode="json")
        assert serialized["start_date"] == "2023-11-27T13:00:00.123456+00:00"
        assert serialized["end_date"] == "2023-12-27T13:00:00.654321+00:00"


class TestCheckUniqueIds:
    """Tests for the check_unique_ids field validator on EpicFreeGames."""

    def test_unique_ids_pass_validation(self) -> None:
        """All unique IDs should pass and return the same list."""
        games: list[EpicGame] = [_make_game("game_1"), _make_game("game_2"), _make_game("game_3")]
        result: list[EpicGame] = EpicFreeGames.check_unique_ids(games)
        assert result == games

    def test_duplicate_single_id_raises_value_error(self) -> None:
        """A single duplicated ID should raise ValueError with the duplicate in message."""
        games: list[EpicGame] = [_make_game("dup_game"), _make_game("dup_game")]
        with pytest.raises(ValueError, match=r"Duplicate game IDs found: \{.*'dup_game'.*\}"):
            EpicFreeGames.check_unique_ids(games)

    def test_multiple_duplicate_ids_raises_and_lists_all(self) -> None:
        """Multiple duplicated IDs should raise and include all duplicate IDs in the message."""
        games: list[EpicGame] = [
            _make_game("a"),
            _make_game("b"),
            _make_game("a"),
            _make_game("c"),
            _make_game("b"),
        ]
        with pytest.raises(ValueError) as excinfo:  # noqa: PT011
            EpicFreeGames.check_unique_ids(games)

        msg = str(excinfo.value)
        assert "Duplicate game IDs found: {" in msg
        assert "'a'" in msg
        assert "'b'" in msg
        # Ensure non-duplicate is not mistakenly reported
        assert "'c'" not in msg


class TestCreateJsonFile:
    def test_create_json_file_writes_expected_structure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        pages_dir: Path = tmp_path / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(tmp_path)

        # Act
        create_json_file()

        # Assert
        output_path: Path = pages_dir / "epic.json"
        assert output_path.exists(), "epic.json should be created in the pages directory"

        data: dict[str, Any] = json.loads(output_path.read_text(encoding="utf-8"))
        assert "free_games" in data
        assert isinstance(data["free_games"], list)
        assert len(data["free_games"]) >= 1

        required_fields: set[str] = {
            "id",
            "game_name",
            "game_url",
            "start_date",
            "end_date",
            "image_link",
            "description",
            "developer",
        }

        ids: list[str] = []
        iso_tz_regex: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}$")
        for game in data["free_games"]:
            assert required_fields.issubset(game.keys())
            ids.append(game["id"])

            # Ensure datetime strings are serialized with +00:00 (or any offset), not 'Z'
            assert iso_tz_regex.match(game["start_date"])
            assert iso_tz_regex.match(game["end_date"])
            assert "Z" not in game["start_date"]
            assert "Z" not in game["end_date"]

        # Ensure IDs are unique
        assert len(ids) == len(set(ids)), "Duplicate game IDs found in generated JSON"

    def test_create_json_file_output_validates_with_pydantic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        (tmp_path / "pages").mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(tmp_path)

        # Act
        create_json_file()

        # Assert
        payload: dict[str, Any] = json.loads((tmp_path / "pages" / "epic.json").read_text(encoding="utf-8"))
        model: EpicFreeGames = EpicFreeGames.model_validate(payload)

        # Basic sanity checks on parsed model
        assert isinstance(model.free_games, list)
        assert len(model.free_games) >= 1

        # Ensure timezone-aware datetimes have been parsed
        for g in model.free_games:
            assert g.start_date.tzinfo is not None
            assert g.end_date.tzinfo is not None


class _DummyResponse:
    def __init__(self, payload: dict[str, Any] | None, is_error: bool = False, status_code: int = 200, reason: str = "OK") -> None:  # noqa: FBT001, FBT002
        self._payload: dict[str, Any] | None = payload
        self.is_error: bool = is_error
        self.status_code: int = status_code
        self.reason_phrase: str = reason

    def json(self) -> dict[str, Any]:
        assert self._payload is not None
        return self._payload


class _DummyClient:
    def __init__(self, response_factory: Callable[[str], _DummyResponse]) -> None:
        self._response_factory = response_factory

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        return None

    def get(self, url: str) -> _DummyResponse:
        # Ensure we request the expected endpoint
        assert url == "https://thelovinator1.github.io/discord-free-game-notifier/epic.json"
        return self._response_factory(url)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


class TestGetEpicFreeGames:
    def test_returns_embeds_for_unposted_unexpired_and_skips_posted_and_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: PLR0914
        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        future_start: datetime.datetime = now - datetime.timedelta(hours=1)
        future_end: datetime.datetime = now + datetime.timedelta(hours=2)

        posted_start: datetime.datetime = now - datetime.timedelta(hours=2)
        posted_end: datetime.datetime = now + datetime.timedelta(hours=2)

        past_start: datetime.datetime = now - datetime.timedelta(days=2)
        past_end: datetime.datetime = now - datetime.timedelta(hours=1)

        payload: dict[str, list[dict[str, str]]] = {
            "free_games": [
                {
                    "id": "game_future_unposted",
                    "game_name": "Future Unposted",
                    "game_url": "https://example.com/game1",
                    "start_date": _iso(future_start),
                    "end_date": _iso(future_end),
                    "image_link": "https://example.com/game1.jpg",
                    "description": "Desc 1",
                    "developer": "Dev 1",
                },
                {
                    "id": "game_future_posted",
                    "game_name": "Future Posted",
                    "game_url": "https://example.com/game2",
                    "start_date": _iso(posted_start),
                    "end_date": _iso(posted_end),
                    "image_link": "https://example.com/game2.jpg",
                    "description": "Desc 2",
                    "developer": "Dev 2",
                },
                {
                    "id": "game_past_unposted",
                    "game_name": "Past Unposted",
                    "game_url": "https://example.com/game3",
                    "start_date": _iso(past_start),
                    "end_date": _iso(past_end),
                    "image_link": "https://example.com/game3.jpg",
                    "description": "Desc 3",
                    "developer": "Dev 3",
                },
            ],
        }

        def response_factory(_: str) -> _DummyResponse:
            return _DummyResponse(payload=payload, is_error=False)

        # Patch httpx.Client to use our dummy client
        monkeypatch.setattr(epic_mod.httpx, "Client", lambda timeout=30: _DummyClient(response_factory))  # type: ignore[assignment]  # noqa: ARG005

        calls: list[tuple[epic_mod.GameService, str]] = []

        def already_posted_stub(game_service: epic_mod.GameService, game_name: str) -> bool:
            calls.append((game_service, game_name))
            return game_name == "game_future_posted"

        monkeypatch.setattr(epic_mod, "already_posted", already_posted_stub)

        results: list[tuple[DiscordEmbed, str]] | None = get_epic_json_games()
        assert isinstance(results, list)
        # Only the future unposted game should be included
        assert len(results) == 1
        embed, game_id = results[0]
        assert game_id == "game_future_unposted"

        assert isinstance(embed, DiscordEmbed)

        # Verify embed structure contains our description and Start/End fields with correct unix timestamps
        embed_dict: dict[str, Any] = embed_to_dict(embed)
        assert embed_dict.get("description") == "Desc 1"

        expected_start_unix = int(future_start.timestamp())
        expected_end_unix = int(future_end.timestamp())

        fields: dict[Any, Any] = {f["name"]: f["value"] for f in embed_dict.get("fields", [])}
        assert fields.get("Start") == f"<t:{expected_start_unix}:R>"
        assert fields.get("End") == f"<t:{expected_end_unix}:R>"

        # Verify already_posted was called for all games with EPIC service
        called_ids: set[str] = {name for _, name in calls}
        assert called_ids == {"game_future_unposted", "game_future_posted", "game_past_unposted"}
        assert all(service is epic_mod.GameService.EPIC for service, _ in calls)

    def test_returns_none_on_http_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def response_factory(_: str) -> _DummyResponse:
            return _DummyResponse(payload=None, is_error=True, status_code=500, reason="Internal Server Error")

        monkeypatch.setattr(epic_mod.httpx, "Client", lambda timeout=30: _DummyClient(response_factory))  # type: ignore[assignment]  # noqa: ARG005

        # Even if already_posted is called, it shouldn't matter because we return early
        monkeypatch.setattr(epic_mod, "already_posted", lambda **kwargs: False)  # noqa: ARG005

        results: list[tuple[DiscordEmbed, str]] | None = get_epic_json_games()
        assert results is None

    def test_returns_empty_list_when_all_games_posted_or_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        posted_game: dict[str, str] = {
            "id": "game_posted",
            "game_name": "Posted",
            "game_url": "https://example.com/posted",
            "start_date": _iso(now - datetime.timedelta(hours=2)),
            "end_date": _iso(now + datetime.timedelta(hours=2)),
            "image_link": "https://example.com/posted.jpg",
            "description": "Posted Desc",
            "developer": "Posted Dev",
        }
        expired_game: dict[str, str] = {
            "id": "game_expired",
            "game_name": "Expired",
            "game_url": "https://example.com/expired",
            "start_date": _iso(now - datetime.timedelta(days=2)),
            "end_date": _iso(now - datetime.timedelta(hours=1)),
            "image_link": "https://example.com/expired.jpg",
            "description": "Expired Desc",
            "developer": "Expired Dev",
        }

        payload: dict[str, list[dict[str, str]]] = {"free_games": [posted_game, expired_game]}

        def response_factory(_: str) -> _DummyResponse:
            return _DummyResponse(payload=payload, is_error=False)

        monkeypatch.setattr(epic_mod.httpx, "Client", lambda timeout=30: _DummyClient(response_factory))  # type: ignore[assignment]  # noqa: ARG005

        def already_posted_stub(game_service: epic_mod.GameService, game_name: str) -> bool:
            return game_name == "game_posted"

        monkeypatch.setattr(epic_mod, "already_posted", already_posted_stub)

        results: list[tuple[DiscordEmbed, str]] | None = get_epic_json_games()
        assert isinstance(results, list)
        assert results == []
