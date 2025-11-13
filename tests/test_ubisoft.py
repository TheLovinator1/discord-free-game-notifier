from __future__ import annotations

import datetime
from typing import Any
from typing import LiteralString

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import HttpUrl
from pydantic import ValidationError

from discord_free_game_notifier.ubisoft import UbisoftFreeGames
from discord_free_game_notifier.ubisoft import UbisoftGame


def _make_game() -> UbisoftGame:
    """Helper to create a valid UbisoftGame instance for testing the serializer.

    Returns:
        UbisoftGame: A valid UbisoftGame instance.
    """
    return UbisoftGame(
        id="test_game",
        game_name="Test Game",
        game_url=HttpUrl("https://example.com/game"),
        start_date=datetime.datetime.now(tz=datetime.UTC),
        end_date=(datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=1)),
        image_link=HttpUrl("https://example.com/test_image.png"),
        description="Test description",
    )


def test_serialize_datetime_returns_plus_zero_for_utc() -> None:
    game: UbisoftGame = _make_game()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
    result: str = game.serialize_datetime(dt)
    assert result == dt.isoformat(), f"Expected {dt.isoformat()} but got {result}"
    assert result.endswith("+00:00"), f"Expected timezone '+00:00' but got {result}"


def test_serialize_datetime_returns_iso_for_naive_datetime() -> None:
    game: UbisoftGame = _make_game()
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0)  # naive datetime  # noqa: DTZ001
    result: str = game.serialize_datetime(dt)
    assert result == dt.isoformat(), f"Expected {dt.isoformat()} but got {result}"
    assert "+" not in result, f"Expected no timezone offset but got {result}"
    assert "Z" not in result, f"Expected no 'Z' timezone but got {result}"


def test_validate_timezone_aware_accepts_aware_datetimes() -> None:
    start = datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC)
    end = datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC)
    game = UbisoftGame(
        id="aware_ok",
        game_name="Aware OK",
        game_url=HttpUrl("https://example.com/game"),
        start_date=start,
        end_date=end,
        image_link=HttpUrl("https://example.com/test_image.png"),
        description="desc",
    )
    assert game.start_date == start, f"Expected start_date to be {start} but got {game.start_date}"
    assert game.end_date == end, f"Expected end_date to be {end} but got {game.end_date}"


def test_validate_timezone_aware_rejects_naive_start_date() -> None:
    start = datetime.datetime(2024, 1, 1, 10, 0, 0)  # noqa: DTZ001
    end = datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC)
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="naive_start",
            game_name="Naive Start",
            game_url=HttpUrl("https://example.com/game"),
            start_date=start,
            end_date=end,
            image_link=HttpUrl("https://example.com/test_image.png"),
            description="desc",
        )
    assert "Input should have timezone info" in str(exc.value), f"Unexpected error message: {exc.value}"

    assert_msg: str = f"Expected 'start_date' in error locations: {exc.value.errors()}"
    assert any("start_date" in err.get("loc", ()) for err in exc.value.errors()), assert_msg


def test_validate_timezone_aware_rejects_naive_end_date() -> None:
    start = datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC)
    end = datetime.datetime(2024, 1, 2, 10, 0, 0)  # noqa: DTZ001
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="naive_end",
            game_name="Naive End",
            game_url=HttpUrl("https://example.com/game"),
            start_date=start,
            end_date=end,
            image_link=HttpUrl("https://example.com/test_image.png"),
            description="desc",
        )
    assert "Input should have timezone info" in str(exc.value), f"Unexpected error message: {exc.value}"
    assert any("end_date" in err.get("loc", ()) for err in exc.value.errors()), f"Expected 'end_date' in error locations: {exc.value}"


def test_validate_timezone_aware_accepts_non_utc_timezone() -> None:
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    start = datetime.datetime(2024, 1, 1, 15, 30, tzinfo=ist)
    end = datetime.datetime(2024, 1, 2, 15, 30, tzinfo=ist)
    game = UbisoftGame(
        id="non_utc_ok",
        game_name="Non-UTC OK",
        game_url=HttpUrl("https://example.com/game"),
        start_date=start,
        end_date=end,
        image_link=HttpUrl("https://example.com/test_image.png"),
        description="desc",
    )
    assert game.start_date.tzinfo is not None, "Expected start_date to be timezone-aware"
    assert game.end_date.tzinfo is not None, "Expected end_date to be timezone-aware"


def test_game_name_max_length() -> None:
    """Test that game_name enforces max_length of 200."""
    long_name: LiteralString = "A" * 201
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="long_name",
            game_name=long_name,
            game_url=HttpUrl("https://example.com/game"),
            start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/test_image.png"),
            description="desc",
        )
    assert "String should have at most 200 characters" in str(exc.value), f"Unexpected error message: {exc.value}"


def test_description_max_length() -> None:
    """Test that description enforces max_length of 4000."""
    long_desc: LiteralString = "A" * 4001
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="long_desc",
            game_name="Game",
            game_url=HttpUrl("https://example.com/game"),
            start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/test_image.png"),
            description=long_desc,
        )
    assert "String should have at most 4000 characters" in str(exc.value), f"Unexpected error message: {exc.value}"


def test_invalid_game_url() -> None:
    """Test that invalid URLs for game_url raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="invalid_url",
            game_name="Game",
            game_url="not-a-url",  # pyright: ignore[reportArgumentType]
            start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://example.com/test_image.png"),
            description="desc",
        )
    assert "url" in str(exc.value).lower(), f"Unexpected error message: {exc.value}"


def test_invalid_image_link() -> None:
    """Test that invalid URLs for image_link raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        UbisoftGame(
            id="invalid_img",
            game_name="Game",
            game_url=HttpUrl("https://example.com/game"),
            start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
            image_link="not-a-url",  # pyright: ignore[reportArgumentType]
            description="desc",
        )
    assert "url" in str(exc.value).lower(), f"Unexpected error message: {exc.value}"


def test_ubisoft_free_games_unique_ids() -> None:
    """Test that UbisoftFreeGames accepts unique game IDs."""
    game1: UbisoftGame = _make_game()
    game2 = UbisoftGame(
        id="test_game2",
        game_name="Test Game 2",
        game_url=HttpUrl("https://example.com/game2"),
        start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
        image_link=HttpUrl("https://example.com/test_image.png"),
        description="Test description 2",
    )
    free_games = UbisoftFreeGames(free_games=[game1, game2])
    assert len(free_games.free_games) == 2, f"Expected 2 unique games but got {len(free_games.free_games)}"


def test_ubisoft_free_games_duplicate_ids() -> None:
    """Test that UbisoftFreeGames rejects duplicate game IDs."""
    game1: UbisoftGame = _make_game()
    game2 = UbisoftGame(
        id="test_game",  # Duplicate ID
        game_name="Test Game 2",
        game_url=HttpUrl("https://example.com/game2"),
        start_date=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2024, 1, 2, 10, 0, tzinfo=datetime.UTC),
        image_link=HttpUrl("https://example.com/test_image.png"),
        description="Test description 2",
    )
    with pytest.raises(ValidationError) as exc:
        UbisoftFreeGames(free_games=[game1, game2])

    assert "Duplicate game IDs found" in str(exc.value), f"Unexpected error message: {exc.value}"


def test_serialize_datetime_with_non_utc_timezone() -> None:
    """Test serialize_datetime with a non-UTC timezone."""
    game: UbisoftGame = _make_game()
    est = datetime.timezone(datetime.timedelta(hours=-5))
    dt = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=est)
    result: str = game.serialize_datetime(dt)
    assert result == dt.isoformat(), f"Expected {dt.isoformat()} but got {result}"
    assert result.endswith("-05:00"), f"Expected timezone '-05:00' but got {result}"


def test_model_dump_json_mode() -> None:
    """Test that model_dump with mode='json' works correctly."""
    game: UbisoftGame = _make_game()
    dumped: dict[str, Any] = game.model_dump(mode="json")
    assert "start_date" in dumped, f"Expected 'start_date' in dumped keys but got {dumped.keys()}"
    assert "end_date" in dumped, f"Expected 'end_date' in dumped keys but got {dumped.keys()}"
    assert isinstance(dumped["start_date"], str), f"Expected 'start_date' to be str but got {type(dumped['start_date'])}"
    assert isinstance(dumped["end_date"], str), f"Expected 'end_date' to be str but got {type(dumped['end_date'])}"
    assert dumped["start_date"].endswith("+00:00"), f"Expected timezone '+00:00' but got {dumped['start_date']}"


def test_ubisoft_free_games_empty_list() -> None:
    """Test UbisoftFreeGames with an empty list of games."""
    free_games = UbisoftFreeGames(free_games=[])
    assert free_games.free_games == [], f"Expected empty list but got {free_games.free_games}"


@given(st.datetimes(timezones=st.just(datetime.UTC)))
def test_serialize_datetime_property_is_iso_format(dt: datetime.datetime) -> None:
    """Property: serialize_datetime always returns ISO format with timezone."""
    game: UbisoftGame = _make_game()
    result: str = game.serialize_datetime(dt)
    # Should be valid ISO format
    assert "T" in result, f"Expected ISO format with 'T' separator but got '{result}'"
    # Should have timezone info
    assert "+" in result or "Z" in result, f"Expected timezone in '{result}'"
    # Should round-trip parse
    parsed: datetime.datetime = datetime.datetime.fromisoformat(result)
    assert parsed.tzinfo is not None, f"Expected timezone-aware datetime from '{result}'"


@given(st.text(min_size=1, max_size=200), st.text(min_size=1, max_size=4000))
def test_ubisoft_game_property_accepts_valid_strings(name: str, desc: str) -> None:
    """Property: UbisoftGame accepts any valid name/description within limits."""
    game = UbisoftGame(
        id="test",
        game_name=name,
        game_url=HttpUrl("https://example.com/game"),
        start_date=datetime.datetime.now(tz=datetime.UTC),
        end_date=(datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=1)),
        image_link=HttpUrl("https://example.com/test_image.png"),
        description=desc,
    )
    assert game.game_name == name
    assert game.description == desc
