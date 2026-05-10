from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Self

import httpx

from discord_free_game_notifier import epic as epic_mod
from discord_free_game_notifier import epic_json as epic_json_mod
from discord_free_game_notifier import epic_mobile as epic_mobile_mod
from discord_free_game_notifier import gog as gog_mod
from discord_free_game_notifier import main as main_mod
from discord_free_game_notifier import steam as steam_mod
from discord_free_game_notifier import steam_json as steam_json_mod
from discord_free_game_notifier import ubisoft as ubisoft_mod

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    import pytest


class _TimeoutClient:
    timeouts: ClassVar[list[object]] = []

    def __init__(self, timeout: object, **kwargs: Any) -> None:  # noqa: ANN401
        _ = kwargs
        self.timeouts.append(timeout)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        return None

    def get(self, *args: Any, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        _ = (args, kwargs)
        msg = "timed out"
        raise httpx.ReadTimeout(msg)


class _RequestErrorClient:
    def __init__(self, timeout: object, **kwargs: Any) -> None:  # noqa: ANN401
        _ = (timeout, kwargs)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        return None

    def get(self, *args: Any, **kwargs: Any) -> httpx.Response:  # noqa: ANN401
        _ = (args, kwargs)
        msg = "[Errno -3] Temporary failure in name resolution"
        raise httpx.ConnectError(msg)


class _FakeLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.exceptions: list[str] = []
        self.debugs: list[str] = []
        self.infos: list[str] = []

    def warning(self, message: str, *args: object) -> None:
        self.warnings.append(message.format(*args))

    def error(self, message: str, *args: object) -> None:
        self.errors.append(message.format(*args))

    def exception(self, message: str, *args: object) -> None:
        self.exceptions.append(message.format(*args))

    def debug(self, message: str, *args: object) -> None:
        self.debugs.append(message.format(*args))

    def info(self, message: str, *args: object) -> None:
        self.infos.append(message.format(*args))


def test_safe_check_service_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(main_mod, "logger", fake_logger)

    def check_function() -> None:
        msg = "timed out"
        raise httpx.ReadTimeout(msg)

    main_mod._safe_check_service("Steam", check_function)

    assert fake_logger.warnings == ["Steam timed out, skipping this check: timed out"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_safe_check_service_request_error_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(main_mod, "logger", fake_logger)

    def check_function() -> None:
        msg = "[Errno -3] Temporary failure in name resolution"
        raise httpx.ConnectError(msg)

    main_mod._safe_check_service("Epic (JSON)", check_function)

    assert fake_logger.warnings == ["Epic (JSON) request failed, skipping this check: [Errno -3] Temporary failure in name resolution"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_json_endpoint_timeouts_are_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    cases: list[tuple[object, Callable[[], object], str]] = [
        (epic_json_mod, epic_json_mod.get_epic_json_games, "Epic free games JSON timed out, skipping this check: timed out"),
        (
            epic_mobile_mod,
            epic_mobile_mod.get_epic_mobile_json_games,
            "Epic mobile free games JSON timed out, skipping this check: timed out",
        ),
        (steam_json_mod, steam_json_mod.get_steam_json_games, "Steam free games JSON timed out, skipping this check: timed out"),
        (ubisoft_mod, ubisoft_mod.get_ubisoft_free_games, "Ubisoft free games JSON timed out, skipping this check: timed out"),
    ]

    for module, check_function, expected_warning in cases:
        _TimeoutClient.timeouts = []
        fake_logger = _FakeLogger()
        monkeypatch.setattr(module.httpx, "Client", _TimeoutClient)  # pyright: ignore[reportAttributeAccessIssue]
        monkeypatch.setattr(module, "logger", fake_logger)

        assert check_function() is None
        assert fake_logger.warnings == [expected_warning]
        assert fake_logger.errors == []
        assert fake_logger.exceptions == []


def test_json_endpoint_request_errors_are_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    cases: list[tuple[object, Callable[[], object], str]] = [
        (
            epic_json_mod,
            epic_json_mod.get_epic_json_games,
            "Epic free games JSON request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
        (
            epic_mobile_mod,
            epic_mobile_mod.get_epic_mobile_json_games,
            "Epic mobile free games JSON request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
        (
            steam_json_mod,
            steam_json_mod.get_steam_json_games,
            "Steam free games JSON request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
        (
            ubisoft_mod,
            ubisoft_mod.get_ubisoft_free_games,
            "Ubisoft free games JSON request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
    ]

    for module, check_function, expected_warning in cases:
        fake_logger = _FakeLogger()
        monkeypatch.setattr(module.httpx, "Client", _RequestErrorClient)  # pyright: ignore[reportAttributeAccessIssue]
        monkeypatch.setattr(module, "logger", fake_logger)

        assert check_function() is None
        assert fake_logger.warnings == [expected_warning]
        assert fake_logger.errors == []
        assert fake_logger.exceptions == []


def test_gog_request_errors_are_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    cases: list[tuple[Callable[[], object], object, str]] = [
        (
            gog_mod.get_free_gog_game,
            None,
            "GOG front page request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
        (
            gog_mod.get_free_gog_game_from_store,
            [],
            "GOG store search request failed, skipping this check: [Errno -3] Temporary failure in name resolution",
        ),
    ]

    for check_function, expected_result, expected_warning in cases:
        fake_logger = _FakeLogger()
        monkeypatch.setattr(gog_mod.httpx, "Client", _RequestErrorClient)
        monkeypatch.setattr(gog_mod, "logger", fake_logger)

        assert check_function() == expected_result
        assert fake_logger.warnings == [expected_warning]
        assert fake_logger.errors == []
        assert fake_logger.exceptions == []


def test_steam_search_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    _TimeoutClient.timeouts = []
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _TimeoutClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)

    assert steam_mod.get_free_steam_games() is None
    assert fake_logger.warnings == ["Steam search timed out, skipping this check: timed out"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_steam_search_request_error_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _RequestErrorClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)

    assert steam_mod.get_free_steam_games() is None
    assert fake_logger.warnings == ["Steam search request failed, skipping this check: [Errno -3] Temporary failure in name resolution"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_steam_detail_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    _TimeoutClient.timeouts = []
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _TimeoutClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)

    more_data = steam_mod._fetch_app_details("123")

    assert more_data == steam_mod.MoreData()
    assert fake_logger.warnings == ["Steam app details timed out for game_id='123', skipping details: timed out"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_steam_detail_request_error_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _RequestErrorClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)

    more_data = steam_mod._fetch_app_details("123")

    assert more_data == steam_mod.MoreData()
    assert fake_logger.warnings == [
        "Steam app details request failed for game_id='123', skipping details: [Errno -3] Temporary failure in name resolution",
    ]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_steam_reviews_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    _TimeoutClient.timeouts = []
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _TimeoutClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)
    more_data = steam_mod.MoreData()

    steam_mod._fetch_reviews("123", more_data)

    assert more_data == steam_mod.MoreData()
    assert fake_logger.warnings == ["Steam reviews timed out for game_id='123', skipping reviews: timed out"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_steam_reviews_request_error_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(steam_mod.httpx, "Client", _RequestErrorClient)
    monkeypatch.setattr(steam_mod, "logger", fake_logger)
    more_data = steam_mod.MoreData()

    steam_mod._fetch_reviews("123", more_data)

    assert more_data == steam_mod.MoreData()
    assert fake_logger.warnings == [
        "Steam reviews request failed for game_id='123', skipping reviews: [Errno -3] Temporary failure in name resolution",
    ]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_epic_graphql_timeout_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(epic_mod, "logger", fake_logger)

    def timeout_get(*args: Any, **kwargs: Any) -> object:  # noqa: ANN401
        _ = (args, kwargs)
        msg = "timed out"
        raise epic_mod.curl_requests.exceptions.Timeout(msg)

    monkeypatch.setattr(epic_mod.curl_requests, "get", timeout_get)

    assert epic_mod._fetch_search_results(5, set(), {}) == ([], False)
    assert fake_logger.warnings == ["Epic GraphQL request timed out, skipping this endpoint: timed out"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []


def test_epic_graphql_request_error_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(epic_mod, "logger", fake_logger)

    def request_error_get(*args: Any, **kwargs: Any) -> object:  # noqa: ANN401
        _ = (args, kwargs)
        msg = "[Errno -3] Temporary failure in name resolution"
        raise epic_mod.curl_requests.exceptions.DNSError(msg)

    monkeypatch.setattr(epic_mod.curl_requests, "get", request_error_get)

    assert epic_mod._fetch_search_results(5, set(), {}) == ([], False)
    assert fake_logger.warnings == ["Epic GraphQL request failed, skipping this endpoint: [Errno -3] Temporary failure in name resolution"]
    assert fake_logger.errors == []
    assert fake_logger.exceptions == []
