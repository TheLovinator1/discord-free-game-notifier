import configparser
import logging
import os
import sys
from pathlib import Path

import typer


class Settings:
    app_dir = typer.get_app_dir("discord_free_game_notifier")
    os.makedirs(app_dir, exist_ok=True)

    config_location: Path = Path(app_dir) / "config.conf"

    if not os.path.isfile(config_location):
        typer.echo("No config file found, creating one...")
        with open(config_location, "w") as config_file:
            config = configparser.ConfigParser()
            config.add_section("config")
            config.set(
                "config",
                "webhook_url",
                "https://discord.com/api/webhooks/1234/567890/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
            )
            config.set("config", "log_level", "INFO")

            config.write(config_file)
        sys.exit(f"Please edit the config file at {config_location}")

    # Read the config file
    config = configparser.ConfigParser()
    config.read(config_location)

    # Get the webhook url from the config file
    webhook_url = config.get("config", "webhook_url")

    # Log severity. Can be CRITICAL, ERROR, WARNING, INFO or DEBUG
    log_level = config.get("config", "log_level")

    logger = logging
    logger.basicConfig(level=log_level)
