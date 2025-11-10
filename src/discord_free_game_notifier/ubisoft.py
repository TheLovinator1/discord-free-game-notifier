from __future__ import annotations

import datetime
import json
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
from discord_free_game_notifier.webhook import send_embed_webhook


class UbisoftGame(BaseModel):
    """Structure for a single Ubisoft free game."""

    id: str
    game_name: str = Field(..., max_length=200)
    game_url: HttpUrl
    start_date: AwareDatetime
    end_date: AwareDatetime
    image_link: HttpUrl
    description: str = Field(..., max_length=4000)

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


class UbisoftFreeGames(BaseModel):
    """Structure for the Ubisoft free games JSON."""

    free_games: list[UbisoftGame]

    @field_validator("free_games")
    @classmethod
    def check_unique_ids(cls, games: list[UbisoftGame]) -> list[UbisoftGame]:
        """Validate that all game IDs are unique.

        Args:
            games: List of Ubisoft games to validate.

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


def create_json_file() -> None:
    """Create or overwrite the ubisoft.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    ac_syndicate = UbisoftGame(
        id="ac_syndicate",
        game_name="Assassin's Creed Syndicate",
        game_url=HttpUrl("https://register.ubisoft.com/acsyndicate/"),
        start_date=datetime.datetime(2023, 11, 27, 13, 0, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2023, 12, 6, 13, 0, 0, tzinfo=datetime.UTC),
        image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/ac_syndicate.png"),
        description="London, 1868. In the heart of the Industrial Revolution, lead your underworld organization and grow your influence to fight those who exploit the less privileged in the name of progress.",  # noqa: E501
    )

    free_games = UbisoftFreeGames(free_games=[ac_syndicate])

    with Path.open(Path("pages/ubisoft.json"), "w", encoding="utf-8") as file:
        json.dump(free_games.model_dump(mode="json"), file, indent=4)
        logger.bind(game_name="Ubisoft").info("Created/updated ubisoft.json")


def get_ubisoft_free_games() -> list[tuple[DiscordEmbed, str]] | None:
    """Get the free games from ubisoft.json.

    Returns:
        Tuple[DiscordEmbed, str]: A tuple containing the Discord embed and the game ID.
    """
    try:
        with httpx.Client(timeout=30) as client:
            ubisoft_json_endpoint = "https://thelovinator1.github.io/discord-free-game-notifier/ubisoft.json"
            response: httpx.Response = client.get(url=ubisoft_json_endpoint)

        if response.is_error:
            logger.error(f"Error fetching Ubisoft free games JSON: {response.status_code} - {response.reason_phrase}")
            return None

        ubisoft_json: UbisoftFreeGames = UbisoftFreeGames.model_validate(response.json())
        free_games: list[UbisoftGame] = ubisoft_json.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            if already_posted(game_service=GameService.UBISOFT, game_name=game.id):
                continue

            unix_start_date = int(game.start_date.timestamp())
            unix_end_date = int(game.end_date.timestamp())

            # Check if the game is still free
            current_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
            if unix_end_date < current_time:
                logger.info(f"{game.game_name} is no longer free, skipping.")
                continue

            embed = DiscordEmbed(description=game.description)

            embed.set_image(url=str(game.image_link))
            embed.set_timestamp()
            embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
            embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
            embed.set_footer(text="Ubisoft")

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Ubisoft.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (httpx.HTTPError, ValidationError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error getting Ubisoft free games from JSON: {e}")
        return None
    else:
        return notified_games


def main() -> None:
    """Main function to create the JSON file and send free game notifications."""
    create_json_file()
    free_games: list[tuple[DiscordEmbed, str]] | None = get_ubisoft_free_games()
    if free_games:
        for embed, game_id in free_games:
            send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.UBISOFT)


if __name__ == "__main__":
    main()
