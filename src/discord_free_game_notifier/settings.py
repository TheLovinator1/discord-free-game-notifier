from __future__ import annotations

import configparser
import sys
import warnings
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from loguru import logger
from platformdirs import user_data_dir
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

dotenv_path: str = find_dotenv()
if dotenv_path:
    logger.info(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, verbose=True)
else:
    logger.warning("No .env file found. Using environment variables or defaults only.")

logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> {extra[game_name]} - {message}"
logger.configure(extra={"game_name": ""})  # Default value
logger.remove()
logger.add(sys.stderr, format=logger_format)

app_dir: str = user_data_dir(appname="discord_free_game_notifier", appauthor="TheLovinator", roaming=True, ensure_exists=True)
config_location: Path = Path(app_dir) / "config.conf"
default_webhook_url = "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config file.

    Environment variables will override config file values if both are set.
    Config file support is deprecated and may be removed in future versions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=False,
    )

    webhook_url: str = Field(default="", description="Main Discord webhook URL for all game notifications")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    gog_webhook: str = Field(default="", description="Discord webhook URL for GOG game notifications")
    steam_webhook: str = Field(default="", description="Discord webhook URL for Steam game notifications")
    epic_webhook: str = Field(default="", description="Discord webhook URL for Epic Games notifications")
    ubisoft_webhook: str = Field(default="", description="Discord webhook URL for Ubisoft game notifications")

    @field_validator("webhook_url", "gog_webhook", "steam_webhook", "epic_webhook", "ubisoft_webhook")
    @classmethod
    def validate_webhook_url(cls, v: str) -> str:
        """Validate that webhook URLs are either empty or valid Discord webhook URLs.

        Args:
            v: The webhook URL string to validate.

        Returns:
            The validated webhook URL string.

        Raises:
            ValueError: If the webhook URL is not empty and doesn't start with the expected Discord URL prefix.
        """
        allowed_prefixes: list[str] = [
            "https://canary.discord.com/api/webhooks/",
            "https://canary.discordapp.com/api/webhooks/",
            "https://discord.com/api/webhooks/",
            "https://discordapp.com/api/webhooks/",
            "https://ptb.discord.com/api/webhooks/",
            "https://ptb.discordapp.com/api/webhooks/",
        ]

        if v and not any(v.startswith(prefix) for prefix in allowed_prefixes):
            msg: str = f"Webhook URL must start with one of {allowed_prefixes}, got: {v}"
            raise ValueError(msg)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is one of the allowed values.

        Args:
            v: The log level string to validate.

        Returns:
            The validated log level string in uppercase.

        Raises:
            ValueError: If the log level is not one of the allowed values.
        """
        allowed_levels: set[str] = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
        v_upper: str = v.upper()
        if v_upper not in allowed_levels:
            msg: str = f"Log level must be one of {allowed_levels}, got: {v}"
            raise ValueError(msg)
        return v_upper


def load_legacy_config() -> dict[str, str]:
    """Load configuration from legacy config file if it exists.

    Returns:
        dict: Dictionary with webhook_url and log_level from config file, or empty strings if file doesn't exist.
    """
    config_webhook_url: str = ""
    config_log_level: str = "INFO"

    if config_location.exists():
        logger.info(f"Loading configuration from {config_location}")
        logger.warning("If you have set WEBHOOK_URL or LOG_LEVEL environment variables, they will override the config file values.")

        config = configparser.ConfigParser()
        config.read(config_location)
        config_webhook_url = config.get(section="config", option="webhook_url", fallback="")
        config_log_level = config.get(section="config", option="log_level", fallback="INFO")

        warnings.warn(
            message="Config file support is deprecated and could be removed in future versions. Please use environment variables instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )

    return {"webhook_url": config_webhook_url, "log_level": config_log_level}


def log_webhook_config(settings_obj: Settings) -> None:
    """Log which webhooks are configured.

    Args:
        settings_obj: The settings instance to check.
    """
    if settings_obj.webhook_url:
        return

    if settings_obj.gog_webhook:
        logger.info("Will be sending GOG games to Discord.")
    if settings_obj.steam_webhook:
        logger.info("Will be sending Steam games to Discord.")
    if settings_obj.epic_webhook:
        logger.info("Will be sending Epic Games to Discord.")
    if settings_obj.ubisoft_webhook:
        logger.info("Will be sending Ubisoft games to Discord.")


def validate_webhooks(settings_obj: Settings) -> None:
    """Validate that at least one webhook is configured.

    Args:
        settings_obj: The settings instance to validate.
    """
    has_webhook: bool = any([
        settings_obj.webhook_url,
        settings_obj.gog_webhook,
        settings_obj.steam_webhook,
        settings_obj.epic_webhook,
        settings_obj.ubisoft_webhook,
    ])
    if not has_webhook:
        msg = "At least one webhook URL must be configured (WEBHOOK_URL, GOG_WEBHOOK, STEAM_WEBHOOK, EPIC_WEBHOOK, or UBISOFT_WEBHOOK)"
        logger.critical(msg)
        sys.exit(1)


def apply_legacy_config(settings_obj: Settings, legacy_config: dict[str, str]) -> None:
    """Apply legacy config values if no environment variable was set.

    Args:
        settings_obj: The settings instance to update.
        legacy_config: The legacy configuration dictionary.
    """
    if legacy_config.get("webhook_url") and not settings_obj.webhook_url:
        settings_obj.webhook_url = legacy_config["webhook_url"]
    if legacy_config.get("log_level") and settings_obj.log_level == "INFO":
        settings_obj.log_level = legacy_config["log_level"]


def initialize_settings() -> Settings:
    """Initialize and validate settings from environment and legacy config.

    Returns:
        Settings: Configured and validated settings instance.
    """
    legacy_config: dict[str, str] = load_legacy_config()

    try:
        settings_obj = Settings()
    except ValueError as e:
        logger.critical(f"Failed to load settings: {e}")
        sys.exit(1)

    apply_legacy_config(settings_obj, legacy_config)
    validate_webhooks(settings_obj)
    log_webhook_config(settings_obj)

    if settings_obj.webhook_url == default_webhook_url:
        logger.warning("Webhook URL is the default value. Please modify it in the .env file.")

    return settings_obj


settings: Settings = initialize_settings()
webhook_url: str = settings.webhook_url
log_level: str = settings.log_level
gog_webhook: str = settings.gog_webhook
steam_webhook: str = settings.steam_webhook
epic_webhook: str = settings.epic_webhook
ubisoft_webhook: str = settings.ubisoft_webhook
