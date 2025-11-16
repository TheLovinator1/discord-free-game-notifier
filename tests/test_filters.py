"""Tests for platform and store filtering settings."""

from __future__ import annotations

import pytest

from discord_free_game_notifier import settings as settings_module


def test_validate_platforms_valid() -> None:
    """Test that valid platform strings are accepted."""
    assert settings_module.Settings.validate_platforms("pc") == "pc"
    assert settings_module.Settings.validate_platforms("android,ios") == "android,ios"
    assert settings_module.Settings.validate_platforms("PC, Android, iOS") == "pc,android,ios"
    assert not settings_module.Settings.validate_platforms("")


def test_validate_platforms_invalid() -> None:
    """Test that invalid platform strings raise ValueError."""
    with pytest.raises(ValueError, match="Invalid platforms"):
        settings_module.Settings.validate_platforms("windows")

    with pytest.raises(ValueError, match="Invalid platforms"):
        settings_module.Settings.validate_platforms("pc,xbox")


def test_validate_stores_valid() -> None:
    """Test that valid store strings are accepted."""
    assert settings_module.Settings.validate_stores("steam") == "steam"
    assert settings_module.Settings.validate_stores("steam,epic") == "steam,epic"
    assert settings_module.Settings.validate_stores("Steam, Epic, GOG") == "steam,epic,gog"
    assert not settings_module.Settings.validate_stores("")


def test_validate_stores_invalid() -> None:
    """Test that invalid store strings raise ValueError."""
    with pytest.raises(ValueError, match="Invalid stores"):
        settings_module.Settings.validate_stores("origin")

    with pytest.raises(ValueError, match="Invalid stores"):
        settings_module.Settings.validate_stores("steam,playstation")


def test_get_enabled_platforms_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that empty platforms returns empty set (all platforms enabled)."""
    monkeypatch.setattr(settings_module, "platforms", "")
    assert settings_module.get_enabled_platforms() == set()


def test_get_enabled_platforms_single(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting enabled platforms with single value."""
    monkeypatch.setattr(settings_module, "platforms", "pc")
    assert settings_module.get_enabled_platforms() == {"pc"}


def test_get_enabled_platforms_multiple(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting enabled platforms with multiple values."""
    monkeypatch.setattr(settings_module, "platforms", "android,ios")
    assert settings_module.get_enabled_platforms() == {"android", "ios"}


def test_get_enabled_stores_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that empty stores returns empty set (all stores enabled)."""
    monkeypatch.setattr(settings_module, "stores", "")
    assert settings_module.get_enabled_stores() == set()


def test_get_enabled_stores_single(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting enabled stores with single value."""
    monkeypatch.setattr(settings_module, "stores", "steam")
    assert settings_module.get_enabled_stores() == {"steam"}


def test_get_enabled_stores_multiple(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting enabled stores with multiple values."""
    monkeypatch.setattr(settings_module, "stores", "steam,epic,gog")
    assert settings_module.get_enabled_stores() == {"steam", "epic", "gog"}


def test_is_platform_enabled_all_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that all platforms are enabled when no filter is set."""
    monkeypatch.setattr(settings_module, "platforms", "")
    assert settings_module.is_platform_enabled("pc") is True
    assert settings_module.is_platform_enabled("android") is True
    assert settings_module.is_platform_enabled("ios") is True


def test_is_platform_enabled_specific(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that only specific platforms are enabled when filter is set."""
    monkeypatch.setattr(settings_module, "platforms", "pc")
    assert settings_module.is_platform_enabled("pc") is True
    assert settings_module.is_platform_enabled("android") is False
    assert settings_module.is_platform_enabled("ios") is False


def test_is_store_enabled_all_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that all stores are enabled when no filter is set."""
    monkeypatch.setattr(settings_module, "stores", "")
    assert settings_module.is_store_enabled("steam") is True
    assert settings_module.is_store_enabled("epic") is True
    assert settings_module.is_store_enabled("gog") is True
    assert settings_module.is_store_enabled("ubisoft") is True


def test_is_store_enabled_specific(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that only specific stores are enabled when filter is set."""
    monkeypatch.setattr(settings_module, "stores", "steam,epic")
    assert settings_module.is_store_enabled("steam") is True
    assert settings_module.is_store_enabled("epic") is True
    assert settings_module.is_store_enabled("gog") is False
    assert settings_module.is_store_enabled("ubisoft") is False
