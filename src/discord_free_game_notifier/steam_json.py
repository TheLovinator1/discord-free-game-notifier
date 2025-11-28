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


class SteamGame(BaseModel):
    """Structure for a single Steam free game."""

    id: str
    game_name: str = Field(..., max_length=200)
    game_url: HttpUrl
    start_date: AwareDatetime
    end_date: AwareDatetime
    image_link: HttpUrl
    description: str = Field(..., max_length=4000)
    developer: str = Field(..., max_length=200)

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


class SteamFreeGames(BaseModel):
    """Structure for the Steam free games JSON."""

    free_games: list[SteamGame]

    @field_validator("free_games")
    @classmethod
    def check_unique_ids(cls, games: list[SteamGame]) -> list[SteamGame]:
        """Validate that all game IDs are unique.

        Args:
            games: List of Steam games to validate.

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
    """Create or overwrite the steam.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    games: list[SteamGame] = [
        # World of Tanks — A Present From Vinnie Pack
        SteamGame(
            id="world_of_tanks_a_present_from_vinnie_pack",
            game_name="World of Tanks — A Present From Vinnie Pack",
            game_url=HttpUrl("https://store.steampowered.com/app/2651870/World_of_Tanks__A_Present_From_Vinnie_Pack/"),
            start_date=datetime.datetime(2023, 12, 1, 11, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 8, 6, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_a_present_from_vinnie_pack.jpg",
            ),
            description='Winter fun has arrived in World of Tanks! Grab Holiday Ops resources to upgrade your Festive Village and an eye-catching decal with this exclusive, time-limited Holiday Ops Gift Pack DLC! Add the bundle to your account for free to get 50 of each Holiday Ops resource (Meteoric Iron, Pure Emerald, Rock Crystal, and Warm Amber) and 3 "Present from Vinnie" decals.',  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # Warframe: Cumulus Collection
        SteamGame(
            id="warframe_cumulus_collection",
            game_name="Warframe: Cumulus Collection",
            game_url=HttpUrl("https://store.steampowered.com/app/2716340/Warframe_Cumulus_Collection/"),
            start_date=datetime.datetime(2023, 12, 18, 21, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 14, 21, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/warframe_cumulus_collection.jpg"),
            description="Cirrus Armor Bundle, Cumulus Syandana, Stratus Pistol Skin, Spektaka Color Palette, and 3-day Resource Booster.",
            developer="Digital Extremes",
        ),
        # World of Tanks — Snatch Gift Pack
        SteamGame(
            id="world_of_tanks_snatch_gift_pack",
            game_name="World of Tanks — Snatch Gift Pack",
            game_url=HttpUrl("https://store.steampowered.com/app/2749320/World_of_Tanks__Snatch_Gift_Pack/"),
            start_date=datetime.datetime(2024, 1, 11, 15, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 1, 24, 0, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_snatch_gift_pack.jpg"),
            description="The Snatch Gift Pack DLC includes:\n- 3 projection decals: Good Luck Charm\n- 3 Large Repair Kits\n- 3 Large First Aid Kits\n- 3 Automatic Fire Extinguishers",  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # World of Tanks Blitz - Bene Gesserit Pack
        SteamGame(
            id="world_of_tanks_blitz_bene_gesserit_pack",
            game_name="World of Tanks Blitz - Bene Gesserit Pack",
            game_url=HttpUrl("https://store.steampowered.com/app/2819910/World_of_Tanks_Blitz__Bene_Gesserit_Pack/"),
            start_date=datetime.datetime(2024, 2, 21, 19, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 3, 7, 0, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_tanks_blitz_bene_gesserit_pack.jpg",
            ),
            description="The Bene Gesserit Pack includes:\n- Lady Jessica Profile Background\n- Bene Gesserit Epic avatar\n- Garage slot\n- 3 days of Premium Account\n- 5 certificates for x5 XP\n- 5 Epic Combat XP boosters",  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # World of Warships x Azur Lane: Free Intro Pack
        SteamGame(
            id="world_of_warships_azur_lane_free_intro_pack",
            game_name="World of Warships x Azur Lane: Free Intro Pack",
            game_url=HttpUrl("https://store.steampowered.com/app/2985620/World_of_Warships__Azur_Lane_Free_Intro_Pack/"),
            start_date=datetime.datetime(2024, 5, 16, 14, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 6, 26, 0, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_azur_lane_free_intro_pack.jpg",
            ),
            description="The Azur Lane: Free Intro Pack includes:\n- 1x Azur Lane container\n- 5x “Azur Lane — Siren” expendable camouflages\n- Access to the Azur Lane Dorm Port",  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # World of Warships x Azur Lane — AL Avrora Free Unlock
        SteamGame(
            id="world_of_warships_azur_lane_al_avrora_free_unlock",
            game_name="World of Warships x Azur Lane — AL Avrora Free Unlock",
            game_url=HttpUrl("https://store.steampowered.com/app/2985560/World_of_Warships__Azur_Lane__AL_Avrora_Free_Unlock/"),
            start_date=datetime.datetime(2024, 5, 16, 14, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2024, 6, 26, 0, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_azur_lane_al_avrora_free_unlock.jpg",
            ),
            description="Play 5 battles to obtain:\n- AL Avrora - Tier III Premium Soviet cruiser\n- A Port slot\n- A Commander with 3 skill points trained for AL Avrora",  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # World of Warships — "8 Years on Steam" Gift Bundle
        SteamGame(
            id="world_of_warships_8_years_on_steam_gift_bundle",
            game_name='World of Warships — "8 Years on Steam" Gift Bundle',
            game_url=HttpUrl("https://store.steampowered.com/app/4126610/World_of_Warships__8_Years_on_Steam_Gift_Bundle/"),
            start_date=datetime.datetime(2025, 11, 3, 0, 0, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2025, 11, 26, 23, 59, 59, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_8_years_on_steam_gift_bundle.jpg",
            ),
            description="8th anniversary of World of Warships on Steam! This package includes:\n- 1x Steam container\n- Steam patch symbol and background\n- Steam permanent camouflage\n- Piece of Cake flag\n- 3 days of Warships Premium Account\n- Access to a two-part combat mission chain (available from 14 November). Complete to receive: Steam Cat permanent camouflage for German Tier V cruiser Königsberg, Steam container, Steam permanent camouflage.",  # noqa: E501
            developer="Wargaming Group Limited",
        ),
        # World of Warships: Holiday Gift
        SteamGame(
            id="world_of_warships_holiday_gift",
            game_name="World of Warships: Holiday Gift",
            game_url=HttpUrl("https://store.steampowered.com/app/4134400/World_of_Warships__Holiday_Gift/"),
            start_date=datetime.datetime(2025, 11, 28, 17, 30, 0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(2026, 1, 6, 18, 0, 0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_holiday_gift.jpg",
            ),
            description='Happy Holidays from World of Warships! Tear into this limited-time free DLC to find the Steam flag, a mission to unlock a Steam permanent camouflage, and a "Christmas and New Year in the Navy" container, which contains an element of the in-game collection of the same name. By gathering all 24 elements, you will obtain a Santa\'s Big Gift container, as well as days of Warships Premium Account!\nThis package contains:\n- 2 "Christmas and New Year in the Navy" container\n- Steam flag\n- Access to a combat mission: Complete 10 battles to receive 1 Steam permanent camouflage',  # noqa: E501
            developer="Wargaming Group Limited",
        ),
    ]

    free_games = SteamFreeGames(free_games=games)

    with Path.open(Path("pages/steam.json"), "w", encoding="utf-8") as file:
        json.dump(free_games.model_dump(mode="json"), file, indent=4)
        logger.bind(game_name="Steam").info("Created/updated steam.json")


def get_steam_json_games() -> list[tuple[DiscordEmbed, str]] | None:
    """Get the free games from steam.json.

    Returns:
        Tuple[DiscordEmbed, str]: A tuple containing the Discord embed and the game ID.
    """
    try:
        with httpx.Client(timeout=30) as client:
            steam_json_endpoint = "https://thelovinator1.github.io/discord-free-game-notifier/steam.json"
            response: httpx.Response = client.get(url=steam_json_endpoint)

        if response.is_error:
            logger.error(f"Error fetching Steam free games JSON: {response.status_code} - {response.reason_phrase}")
            return None

        steam_json: SteamFreeGames = SteamFreeGames.model_validate(response.json())
        free_games: list[SteamGame] = steam_json.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            if already_posted(game_service=GameService.STEAM, game_name=game.id):
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
            embed.set_footer(text=game.developer)

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Steam.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (httpx.HTTPError, ValidationError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error getting Steam free games from JSON: {e}")
        return None
    else:
        return notified_games


def main() -> None:
    """Main function to generate steam.json only.

    Notification/"check" logic has been moved to a dedicated module
    `discord_free_game_notifier.steam_json_check` so generation and
    notification can be run independently.
    """
    create_json_file()


if __name__ == "__main__":
    main()
