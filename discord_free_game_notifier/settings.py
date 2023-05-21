import configparser
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_dir

load_dotenv()
app_dir: str = user_data_dir(
    "discord_free_game_notifier",
    "TheLovinator",
    roaming=True,
)
Path.mkdir(Path(app_dir), exist_ok=True)

config_location: Path = Path(app_dir) / "config.conf"

if not Path.is_file(config_location):
    logging.info("No config file found, creating one...")
    with Path.open(config_location, "w", encoding="UTF-8") as config_file:
        config = configparser.ConfigParser()
        config.add_section("config")
        config.set(
            "config",
            "webhook_url",
            "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
        )
        config.set("config", "log_level", "INFO")

        config.write(config_file)
    logging.info("Please edit the config file at {} or use environment variables.", config_location)

# Read the config file
config = configparser.ConfigParser()
config.read(config_location)

# Get the webhook url from the config file
config_webhook_url: str = config.get("config", "webhook_url")

# Log severity. Can be CRITICAL, ERROR, WARNING, INFO or DEBUG.
config_log_level: str = config.get("config", "log_level")

# If user has environment variable set, use that instead
webhook_url: str = os.getenv("WEBHOOK_URL", config_webhook_url)
log_level: str = os.getenv("LOG_LEVEL", config_log_level)

# TODO: Add tests for these
steam_icon: str = os.getenv("STEAM_ICON", "https://lovinator.space/Steam_logo.png")
gog_icon: str = os.getenv("GOG_ICON", "https://lovinator.space/gog_logo.png")
epic_icon: str = os.getenv("EPIC_ICON", "https://lovinator.space/Epic_Games_logo.png")

logger = logging
logger.basicConfig(level=log_level)

logger.debug("Config location: {}", config_location)
logger.debug("Webhook url: {}", webhook_url)
