"""Manual entry module for Epic Games mobile (Android/iOS) games.

This module allows you to manually send notifications about free mobile games
on Epic Games Store to Discord webhooks. Since mobile games are not included
in the Epic Games API, this provides a way to notify users about mobile-specific
promotions.

Environment variables for local testing:
- EPIC_MOBILE_LOCAL=1    Use local pages/epic_mobile.json instead of remote URL
- EPIC_MOBILE_PREVIEW=1  Print embeds to console instead of sending to Discord
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

import httpx
from discord_webhook import DiscordEmbed
from loguru import logger
from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic import ValidationError
from pydantic import field_serializer
from pydantic import field_validator

from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import GameService


class EpicMobileGame(BaseModel):
    """Structure for a single Epic mobile game."""

    id: str
    game_name: str = Field(..., max_length=200)
    game_url: HttpUrl
    start_date: AwareDatetime
    end_date: AwareDatetime
    image_link: HttpUrl
    description: str = Field(..., max_length=4000)
    developer: str = Field(..., max_length=200)
    platform: str = Field(..., max_length=50)
    # Optional structured fields for better embed formatting
    includes: list[str] | None = None
    quick_links: dict[str, HttpUrl] | None = None

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_timezone_aware(cls, dt: datetime.datetime) -> datetime.datetime:
        """Validate that datetime is timezone-aware.

        Args:
            dt: The datetime object to validate.

        Returns:
            The validated datetime object.

        Raises:
            ValueError: If the datetime is not timezone-aware.
        """
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            msg: str = "Datetime must be timezone-aware"
            raise ValueError(msg)
        return dt

    @field_serializer("start_date", "end_date")
    def serialize_datetime(self, dt: datetime.datetime) -> str:
        """Serialize datetime with +00:00 format instead of Z.

        By default, Pydantic serializes UTC datetimes as "2023-11-27T13:00:00Z".
        This custom serializer ensures we use "+00:00" format to match the format
        used by the previous implementation before migrating to Pydantic.

        Args:
            dt: The datetime object to serialize.

        Returns:
            ISO 8601 formatted string with timezone offset (+00:00 format).
        """
        return dt.isoformat()

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate that platform is a valid value.

        Args:
            v: The platform string to validate.

        Returns:
            The validated platform string.

        Raises:
            ValueError: If the platform is not valid.
        """
        valid_platforms: set[str] = {"Android", "iOS", "Android & iOS"}
        if v not in valid_platforms:
            msg: str = f"Platform must be one of {valid_platforms}, got: {v}"
            raise ValueError(msg)
        return v


class EpicMobileFreeGames(BaseModel):
    """Structure for the Epic mobile free games JSON."""

    free_games: list[EpicMobileGame]

    @field_validator("free_games")
    @classmethod
    def check_unique_ids(cls, games: list[EpicMobileGame]) -> list[EpicMobileGame]:
        """Validate that all game IDs are unique.

        Args:
            games: List of Epic mobile games to validate.

        Returns:
            The validated list of games.

        Raises:
            ValueError: If duplicate game IDs are found.
        """
        ids: list[str] = [game.id for game in games]
        if len(ids) != len(set(ids)):
            duplicates: list[str] = [game_id for game_id in ids if ids.count(game_id) > 1]
            msg: str = f"Duplicate game IDs found: {set(duplicates)}"
            raise ValueError(msg)
        return games


def _load_epic_mobile_raw_from_source() -> dict[str, EpicMobileGame] | None:
    """Load Epic mobile JSON either from local file or remote URL.

    Controlled by env var EPIC_MOBILE_LOCAL=1 to use local pages/epic_mobile.json.

    Returns:
        dict | None: Raw JSON object for Epic mobile free games, or None on error.
    """
    use_local: bool = os.getenv("EPIC_MOBILE_LOCAL", "0") == "1"
    if use_local:
        local_path = Path("pages/epic_mobile.json")
        if not local_path.exists():
            logger.error("Local pages/epic_mobile.json not found. Generate it first.")
            return None
        logger.info("Using local pages/epic_mobile.json for Epic mobile free games (EPIC_MOBILE_LOCAL=1).")
        with local_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    with httpx.Client(timeout=30) as client:
        epic_mobile_json_endpoint = "https://thelovinator1.github.io/discord-free-game-notifier/epic_mobile.json"
        response: httpx.Response = client.get(url=epic_mobile_json_endpoint)
    if response.is_error:
        logger.error(f"Error fetching Epic mobile free games JSON: {response.status_code} - {response.reason_phrase}")
        return None
    return response.json()


def create_json_file() -> None:
    """Create or overwrite the epic_mobile.json file with the free mobile games.

    The bot will use this file to check if there are any new free mobile games.
    """
    # Define event window datetimes (UTC)
    start_dt = datetime.datetime(2025, 11, 6, 16, 0, 0, tzinfo=datetime.UTC)
    end_dt = datetime.datetime(2025, 11, 13, 16, 0, 0, tzinfo=datetime.UTC)

    # Precompute unix timestamps for Discord timestamp tokens
    end_unix = int(end_dt.timestamp())

    games_list: list[EpicMobileGame] = [
        # Idle Champions - Nixie's Champions of Renown Pack (Epic Exclusive mobile login bundle)
        # Provided by user; ensure dates use UTC and +00:00 format
        EpicMobileGame(
            id="idle_champions_nixies_champions_of_renown_pack",
            game_name="Idle Champions - Nixie's Champions of Renown Pack",
            game_url=HttpUrl(
                "https://store.epicgames.com/purchase?offers=1-7e508f543b05465abe3a935960eb70ac-c9f2ce27f1c44ba9ad0cf4260f9e709e&offers=1-7e508f543b05465abe3a935960eb70ac-dd07843b88f64ee898a4ea415c6dcb17",
            ),
            start_date=start_dt,
            end_date=end_dt,
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/idle_champions_nixie.png"),
            description=(
                "**Nixie's Champions of Renown Bundle Pack (Epic Exclusive)** — free by "
                "logging into Idle Champions via the Epic Games Store before "
                f"<t:{end_unix}:R>."
            ),
            developer="Codename Entertainment",
            platform="Android & iOS",
            includes=[
                "Unlocks: Nixie (Seat 1), Mehen (Seat 3), Shadowheart (Seat 6), Freely (Seat 7), Tess (Seat 8)",
                "Exclusive Familiar: Sting the Scorpion",
                "Platinum Chests: 32 each for Nixie, Mehen, Shadowheart, Freely, Tess (2 guaranteed Shiny equipment cards per Champion)",
                "1x Potion of the Gem Hunter, 1x Potion of the Gold Hunter (2-week buff)",
            ],
            quick_links={
                "Buy Both": HttpUrl(
                    "https://store.epicgames.com/purchase?offers=1-7e508f543b05465abe3a935960eb70ac-c9f2ce27f1c44ba9ad0cf4260f9e709e&offers=1-7e508f543b05465abe3a935960eb70ac-dd07843b88f64ee898a4ea415c6dcb17",
                ),
                "Buy Android": HttpUrl(
                    "https://store.epicgames.com/purchase?offers=1-7e508f543b05465abe3a935960eb70ac-c9f2ce27f1c44ba9ad0cf4260f9e709e",
                ),
                "Buy iOS": HttpUrl(
                    "https://store.epicgames.com/purchase?offers=1-7e508f543b05465abe3a935960eb70ac-dd07843b88f64ee898a4ea415c6dcb17",
                ),
                "Store Android": HttpUrl("https://store.epicgames.com/p/idle-champions-of-the-forgotten-realms-android-6df748"),
                "Store iOS": HttpUrl("https://store.epicgames.com/p/idle-champions-of-the-forgotten-realms-ios-77e761"),
                "Transactions": HttpUrl("https://www.epicgames.com/account/transactions?productName=egs"),
            },
        ),
    ]

    free_games = EpicMobileFreeGames(free_games=games_list)

    with Path.open(Path("pages/epic_mobile.json"), "w", encoding="utf-8") as file:
        json.dump(free_games.model_dump(mode="json"), file, indent=4)
        logger.info("Created/updated epic_mobile.json")


def _build_embed_for_game(game: EpicMobileGame) -> DiscordEmbed:
    """Build a Discord embed for a given Epic mobile game.

    Returns:
        DiscordEmbed: The constructed embed ready to send.
    """
    unix_start_date = int(game.start_date.timestamp())
    unix_end_date = int(game.end_date.timestamp())

    embed = DiscordEmbed(description=game.description)
    embed.set_image(url=str(game.image_link))
    embed.set_timestamp()

    # Basic fields
    embed.add_embed_field(name="Platform", value=game.platform, inline=True)
    start_ts_rel: str = f"<t:{unix_start_date}:R>"
    start_ts_full: str = f"<t:{unix_start_date}:f>"
    end_ts_rel: str = f"<t:{unix_end_date}:R>"
    end_ts_full: str = f"<t:{unix_end_date}:f>"
    embed.add_embed_field(name="Start", value=f"{start_ts_rel} ({start_ts_full})", inline=True)
    embed.add_embed_field(name="End", value=f"{end_ts_rel} ({end_ts_full})", inline=True)

    # Optional structured sections
    if game.includes:
        includes_value: str = "\n".join(f"• {item}" for item in game.includes)
        embed.add_embed_field(name="Includes", value=includes_value, inline=False)

    if game.quick_links:
        links_joined: str = " \u2022 ".join(f"[{label}]({url})" for label, url in game.quick_links.items())
        embed.add_embed_field(name="Links", value=links_joined, inline=False)

    # Footer and author
    embed.set_footer(text=game.developer)
    icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Epic.png"
    embed.set_author(name=f"{game.game_name} ({game.platform})", url=str(game.game_url), icon_url=icon_url)
    return embed


def get_epic_mobile_json_games() -> list[tuple[DiscordEmbed, str]] | None:
    """Get the free mobile games from epic_mobile.json.

    Returns:
        list[tuple[DiscordEmbed, str]] | None: A list of tuples containing the Discord embed and the game ID, or None if error.
    """
    try:
        epic_mobile_raw: dict[str, EpicMobileGame] | None = _load_epic_mobile_raw_from_source()
        if epic_mobile_raw is None:
            return None

        epic_mobile_json: EpicMobileFreeGames = EpicMobileFreeGames.model_validate(epic_mobile_raw)
        free_games: list[EpicMobileGame] = epic_mobile_json.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            if already_posted(game_service=GameService.EPIC, game_name=game.id):
                continue

            # Check if the game is still free
            current_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
            unix_end_date = int(game.end_date.timestamp())
            if unix_end_date < current_time:
                logger.info(f"{game.game_name} is no longer free, skipping.")
                continue

            embed: DiscordEmbed = _build_embed_for_game(game)
            notified_games.append((embed, game.id))

        # Optional preview mode: just print embeds instead of sending (useful for local dev)
        if os.getenv("EPIC_MOBILE_PREVIEW", "0") == "1":
            for embed, game_id in notified_games:
                logger.info(f"[PREVIEW] Would send Epic Mobile game: {game_id}")
                logger.info(f"[PREVIEW] Description:\n{embed.description}")
            return []  # Return empty so caller treats as 'nothing to send'
    except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError, ValidationError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error getting Epic mobile free games from JSON: {e}")
        return None
    else:
        return notified_games


def main() -> None:
    """Main function to generate epic_mobile.json only.

    Notification/"check" logic should be in a dedicated module
    `discord_free_game_notifier.epic_mobile_check` so generation and
    notification can be run independently.
    """
    create_json_file()


if __name__ == "__main__":
    main()
