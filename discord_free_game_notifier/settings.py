"""Settings are stored in a config file.
On first run, a config file is created and the user is asked to edit
it. On Windows, the config file is stored in
%appdata%/TheLovinator/discord_free_game_notifier
"""
import configparser
import logging
import os
import sys
from pathlib import Path

from platformdirs import user_data_dir

app_dir = user_data_dir(
    "discord_free_game_notifier",
    "TheLovinator",
    roaming=True,
)
os.makedirs(app_dir, exist_ok=True)

config_location: Path = Path(app_dir) / "config.conf"

if not os.path.isfile(config_location):
    print("No config file found, creating one...")
    with open(config_location, "w", encoding="UTF-8") as config_file:
        config = configparser.ConfigParser()
        config.add_section("config")
        config.set(
            "config",
            "webhook_url",
            "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",  # noqa: E501, pylint: disable=line-too-long
        )
        config.set("config", "log_level", "INFO")

        config.write(config_file)
    sys.exit(f"Please edit the config file at {config_location}")

# Read the config file
config = configparser.ConfigParser()
config.read(config_location)

# Get the webhook url from the config file
config_webhook_url = config.get("config", "webhook_url")

# Log severity. Can be CRITICAL, ERROR, WARNING, INFO or DEBUG
config_log_level = config.get("config", "log_level")

# If user has environment variable set, use that instead
webhook_url = os.getenv("WEBHOOK_URL", config_webhook_url)
log_level = os.getenv("LOG_LEVEL", config_log_level)

logger = logging
logger.basicConfig(level=log_level)

logger.debug(f"Config location: {config_location}")
logger.debug(f"Webhook url: {webhook_url}")
