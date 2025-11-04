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


class EpicGame(BaseModel):
    """Structure for a single Epic free game."""

    id: str
    game_name: str = Field(..., max_length=200)
    game_url: HttpUrl
    start_date: AwareDatetime
    end_date: AwareDatetime
    image_link: HttpUrl
    description: str = Field(..., max_length=4000)
    developer: str = Field(..., max_length=200)

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


class EpicFreeGames(BaseModel):
    """Structure for the Epic free games JSON."""

    free_games: list[EpicGame]

    @field_validator("free_games")
    @classmethod
    def check_unique_ids(cls, games: list[EpicGame]) -> list[EpicGame]:
        """Validate that all game IDs are unique.

        Args:
            games: List of Epic games to validate.

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
    """Create or overwrite the Epic.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    games_list: list[EpicGame] = [
        EpicGame(
            id="the_sims_4_my_first_pet_stuff",
            game_name="The Sims™ 4 My First Pet Stuff",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/the-sims-4--my-first-pet-stuff"),
            start_date=datetime.datetime(year=2023, month=12, day=1, hour=11, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=9, hour=18, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/the_sims_4_my_first_pet_stuff.jpg"),
            description="Welcome home a new small animal and show love for Cats and Dogs with The Sims™ 4 My First Pet Stuff.\n\n[Instant Checkout](https://store.epicgames.com/purchase?offers=1-2a14cf8a83b149919a2399504e5686a6-7002cdb1eb2543da85ac8a3c4c6d71d5#/)",
            developer="Maxis",
        ),
        EpicGame(
            id="fall_guys_giddy_gift",
            game_name="Fall Guys - Giddy Gift",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/fall-guys--giddy-gift"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/fall_guys_giddy_gift.jpg"),
            description="May we 'present' the free Giddy Gift costume! Wrap up this Winter & earn a crown or two in Fall Guys\n\nIncludes: Giddy Gift (Whole Costume)",  # noqa: E501
            developer="Mediatonic",
        ),
        EpicGame(
            id="disney_speedstorm_monochromatic_pack",
            game_name="Disney Speedstorm - Monochromatic Pack",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/disney-speedstorm--monochromatic-pack"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/disney_speedstorm_monochromatic_pack.jpg",
            ),
            description="This pack includes:\n• Racing Suit for Goofy: Monochromatic Classic\n• Kart livery for Goofy: Monochromatic Classic\n• Chip n' Dale Rare Crew Shards\n• 5 Universal Box Credits",  # noqa: E501
            developer="Gameloft",
        ),
        EpicGame(
            id="dark_justiciar_shadowheart_party_pack",
            game_name="Dark Justiciar Shadowheart Party Pack",
            game_url=HttpUrl(
                "https://store.epicgames.com/en-US/p/idle-champions-of-the-forgotten-realms--dark-justiciar-shadow-heart-party-pack",
            ),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl(
                "https://thelovinator1.github.io/discord-free-game-notifier/images/dark_justiciar_shadowheart_party_pack.jpg",
            ),
            description="This pack unlocks the first 3 Baldur's Gate 3 Champions: Lae'zel, Shadowheart, and Astarion. Also included are 7 Gold Champion Chests for each and an exclusive Skin & Feat Shadowheart!",  # noqa: E501
            developer="Codename Entertainment",
        ),
        EpicGame(
            id="warframe_holiday_sale_2023",
            game_name="Warframe - Holiday Sale 2023",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/warframe"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/warframe_holiday_sale_2023.jpg"),
            description="Come celebrate the Epic Games Holiday Sale with us and claim the Atterax Weapon, a 7-Day Credit Booster and 7-Day Affinity Booster for free!\nPlayers who launch and log in to WARFRAME on Epic Games Store during the promotional period will receive an inbox message with free content upon login into the game. ",  # noqa: E501
            developer="Digital Extremes",
        ),
        EpicGame(
            id="honkai_impact_holiday_sale_2023",
            game_name="Honkai Impact - Holiday Sale 2023",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/honkai-impact-3rd"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/honkai_impact_holiday_sale_2023.jpg"),
            description="Celebrate the Epic Games Holiday Sale and get 500 Asterites and 100,000 Coins for free!\nPlayers who log in to Honkai Impact 3rd on Epic Games Store during the event period will receive the bundle via an in-game mail within one week.",  # noqa: E501
            developer="miHoYo Limited",
        ),
        EpicGame(
            id="synced_holiday_sale_2023",
            game_name="SYNCED: Winterfest Bundle",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/synced--winterfest-bundle"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/synced_holiday_sale_2023.jpg"),
            description="Unlock this Bundle of SYNCED to obtain new Runner and weapon skins, and embrace fresh challenges in the new season - Lambent Dawn.",  # noqa: E501
            developer="NExT Studios",
        ),
        EpicGame(
            id="world_of_warships_holiday_sale_2023",
            game_name="World of Warships — Frosty Celebration Pack",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/world-of-warships--frosty-celebration-pack"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_holiday_sale_2023.jpg"),
            description="Embrace the magic of the winter holidays with this free DLC featuring cruiser Ning Hai and the enchanting allure of even more Premium ships that could drop from five festive Santa's Gift containers.",  # noqa: E501
            developer="Wargaming",
        ),
        EpicGame(
            id="eve_online_superluminal_pack",
            game_name="EVE Online - Superluminal Pack",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/eve-online--superluminal-pack"),
            start_date=datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/eve_online_superluminal_pack.jpg"),
            description="The Superluminal Pack is a limited-time-only FREE giveaway exclusive to Epic! It contains Semiotique Superluminal SKINs for the Heron, Magnate, Imicus, and Probe as well as unique Superluminal clothing!",  # noqa: E501
            developer="CCP Games",
        ),
        EpicGame(
            id="epic_mega_sale_2024",
            game_name="Epic Games MEGA Sale 2024",
            game_url=HttpUrl("https://store.epicgames.com/en-US/free-games"),
            start_date=datetime.datetime(year=2024, month=5, day=16, hour=18, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=6, day=12, hour=0, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/epic_mega_sale_2024.jpg"),
            description="Free Epic stuff:\n- [Disney Speedstorm Monochromatic Pack - Racer Stitch](https://store.epicgames.com/en-US/p/disney-speedstorm--racer-stitch)\n- [Genshin Impact MEGA Sale Bundle](https://store.epicgames.com/en-US/p/genshin-impact--mega-sale-bundle)\n- [Honkai: Star Rail MEGA Sale Bundle](https://store.epicgames.com/en-US/p/honkai-star-rail--epic-mega-sale-event-bundle)\n- [Fortnite Overclocked Combo Pack](https://store.epicgames.com/en-US/p/fortnite--overclocked-combo-pack)\n- [Fall Guys - Soda Crown](https://store.epicgames.com/en-US/p/fall-guys--soda-crown)\n- [1 Month of Discord Nitro](https://store.epicgames.com/en-US/p/discord--discord-nitro)\n- [Dauntless Golden Drake's Eye Bundle](https://store.epicgames.com/en-US/p/dauntless--golden-drakes-eye-bundle)\n- [Warframe Pyra Syandana and Fire Color Picker](https://store.epicgames.com/en-US/p/warframe)\n- [Honkai Impact 3rd Bundle](https://store.epicgames.com/en-US/p/honkai-impact-3rd)",  # noqa: E501
            developer="Epic Games et al.",
        ),
        EpicGame(
            id="wuthering_waves_echo_starter_pack",
            game_name="Wuthering Waves - Echo Starter Pack",
            game_url=HttpUrl("https://store.epicgames.com/en-US/p/wuthering-waves-echo-starter-pack-eae1db"),
            start_date=datetime.datetime(year=2024, month=5, day=23, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            end_date=datetime.datetime(year=2024, month=6, day=23, hour=16, minute=0, second=0, tzinfo=datetime.UTC),
            image_link=HttpUrl("https://thelovinator1.github.io/discord-free-game-notifier/images/wuthering_waves_echo_starter_pack.jpg"),
            description="The Echo Starter Pack includes:\n- 1 Incomplete Echo\n- 10 Premium Tuner\n- 5 Advanced Sealed Tube",
            developer="KURO GAMES",
        ),
    ]

    free_games = EpicFreeGames(free_games=games_list)

    with Path.open(Path("pages/epic.json"), "w", encoding="utf-8") as file:
        json.dump(free_games.model_dump(mode="json"), file, indent=4)
        logger.info("Created/updated epic.json")


def get_epic_free_games() -> list[tuple[DiscordEmbed, str]] | None:
    """Get the free games from epic.json.

    Returns:
        Tuple[DiscordEmbed, str]: A tuple containing the Discord embed and the game ID.
    """
    try:
        with httpx.Client(timeout=30) as client:
            epic_json_endpoint = "https://thelovinator1.github.io/discord-free-game-notifier/epic.json"
            response: httpx.Response = client.get(url=epic_json_endpoint)

        if response.is_error:
            logger.error(f"Error fetching Epic free games JSON: {response.status_code} - {response.reason_phrase}")
            return None

        epic_json: EpicFreeGames = EpicFreeGames.model_validate(response.json())
        free_games: list[EpicGame] = epic_json.free_games

        notified_games: list[tuple[DiscordEmbed, str]] = []
        for game in free_games:
            if already_posted(game_service=GameService.EPIC, game_name=game.id):
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

            icon_url = "https://thelovinator1.github.io/discord-free-game-notifier/images/Epic.png"
            embed.set_author(name=f"{game.game_name}", url=str(game.game_url), icon_url=icon_url)

            notified_games.append((embed, game.id))
    except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError, ValidationError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error getting Epic free games from JSON: {e}")
        return None
    else:
        return notified_games


def main() -> None:
    """Main function to generate epic.json only.

    Notification/"check" logic has been moved to a dedicated module
    `discord_free_game_notifier.epic_json_check` so generation and
    notification can be run independently.
    """
    create_json_file()


if __name__ == "__main__":
    main()
