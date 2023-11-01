import configparser
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from loguru import logger
from platformdirs import user_data_dir

load_dotenv(dotenv_path=find_dotenv(), verbose=True)

app_dir: str = user_data_dir("discord_free_game_notifier", "TheLovinator", roaming=True)
Path.mkdir(Path(app_dir), exist_ok=True)

config_location: Path = Path(app_dir) / "config.conf"
default_webhook_url: str = "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"

config_webhook_url = ""
config_log_level = "INFO"

if config_location.exists():
    config = configparser.ConfigParser()
    config.read(config_location)
    config_webhook_url: str = config.get("config", "webhook_url")
    config_log_level: str = config.get("config", "log_level")

webhook_url: str = os.getenv("WEBHOOK_URL", config_webhook_url)
log_level: str = os.getenv("LOG_LEVEL", config_log_level)
steam_icon: str = os.getenv("STEAM_ICON", "https://lovinator.space/Steam_logo.png")
gog_icon: str = os.getenv("GOG_ICON", "https://lovinator.space/gog_logo.png")
epic_icon: str = os.getenv("EPIC_ICON", "https://lovinator.space/Epic_Games_logo.png")

gog_webhook: str = os.getenv("GOG_WEBHOOK", "")
steam_webhook: str = os.getenv("STEAM_WEBHOOK", "")
epic_webhook: str = os.getenv("EPIC_WEBHOOK", "")

if not webhook_url:
    if gog_webhook:
        logger.info("Will be sending GOG games to Discord.")
    if steam_webhook:
        logger.info("Will be sending Steam games to Discord.")
    if epic_webhook:
        logger.info("Will be sending Epic Games to Discord.")
    if not gog_webhook and not steam_webhook and not epic_webhook:
        msg: str = "Please set the WEBHOOK_URL environment variable."
        logger.critical(msg)
        sys.exit(1)
