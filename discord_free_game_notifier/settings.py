import configparser
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from platformdirs import user_data_dir

load_dotenv()
app_dir: str = user_data_dir(
    "discord_free_game_notifier",
    "TheLovinator",
    roaming=True,
)
Path.mkdir(Path(app_dir), exist_ok=True)

config_location: Path = Path(app_dir) / "config.conf"
default_webhook_url: str = (
    "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
)

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

steam_icon: str = os.getenv("STEAM_ICON", "https://lovinator.space/Steam_logo.png")
gog_icon: str = os.getenv("GOG_ICON", "https://lovinator.space/gog_logo.png")
epic_icon: str = os.getenv("EPIC_ICON", "https://lovinator.space/Epic_Games_logo.png")

gog_webhook: str = os.getenv("GOG_WEBHOOK", "")
steam_webhook: str = os.getenv("STEAM_WEBHOOK", "")
epic_webhook: str = os.getenv("EPIC_WEBHOOK", "")

logger.debug("Config location: {}", config_location)
logger.debug("Webhook url: {}", webhook_url)
