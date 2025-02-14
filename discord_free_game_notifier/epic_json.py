"""Check https://thelovinator1.github.io/discord-free-game-notifier/epic.json for free games.

This is for games that are not found by epic.py.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import TypedDict

import requests
from discord_webhook import DiscordEmbed
from loguru import logger

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook


class FreeGame(TypedDict):
    """A free game from Epic.json."""

    id: str
    game_name: str
    game_url: str
    start_date: str  # or datetime if you parse it
    end_date: str  # or datetime if you parse it
    image_link: str
    description: str
    developer: str


class FreeGamesResponse(TypedDict):
    """The response from Epic.json."""

    free_games: list[FreeGame]


def create_json_file() -> None:
    """Create or overwrite the Epic.json file with the free games.

    The bot will use this file to check if there are any new free games.
    """
    free_games: dict[str, list[dict[str, str]]] = {
        "free_games": [
            {
                "id": "the_sims_4_my_first_pet_stuff",
                "game_name": "The Sims™ 4 My First Pet Stuff",
                "game_url": "https://store.epicgames.com/en-US/p/the-sims-4--my-first-pet-stuff",
                "start_date": datetime.datetime(year=2023, month=12, day=1, hour=11, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=9, hour=18, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/the_sims_4_my_first_pet_stuff.jpg",
                "description": "Welcome home a new small animal and show love for Cats and Dogs with The Sims™ 4 My First Pet Stuff.\n\n[Instant Checkout](https://store.epicgames.com/purchase?offers=1-2a14cf8a83b149919a2399504e5686a6-7002cdb1eb2543da85ac8a3c4c6d71d5#/)",  # noqa: E501
                "developer": "Maxis",
            },
            {
                "id": "fall_guys_giddy_gift",
                "game_name": "Fall Guys - Giddy Gift",
                "game_url": "https://store.epicgames.com/en-US/p/fall-guys--giddy-gift",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/fall_guys_giddy_gift.jpg",
                "description": "May we 'present' the free Giddy Gift costume! Wrap up this Winter & earn a crown or two in Fall Guys\n\nIncludes: Giddy Gift (Whole Costume)",  # noqa: E501
                "developer": "Mediatonic",
            },
            {
                "id": "disney_speedstorm_monochromatic_pack",
                "game_name": "Disney Speedstorm - Monochromatic Pack",
                "game_url": "https://store.epicgames.com/en-US/p/disney-speedstorm--monochromatic-pack",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/disney_speedstorm_monochromatic_pack.jpg",
                "description": "This pack includes:\n• Racing Suit for Goofy: Monochromatic Classic\n• Kart livery for Goofy: Monochromatic Classic\n• Chip n' Dale Rare Crew Shards\n• 5 Universal Box Credits",  # noqa: E501
                "developer": "Gameloft",
            },
            {
                "id": "dark_justiciar_shadowheart_party_pack",
                "game_name": "Dark Justiciar Shadowheart Party Pack",
                "game_url": "https://store.epicgames.com/en-US/p/idle-champions-of-the-forgotten-realms--dark-justiciar-shadow-heart-party-pack",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/dark_justiciar_shadowheart_party_pack.jpg",
                "description": "This pack unlocks the first 3 Baldur's Gate 3 Champions: Lae'zel, Shadowheart, and Astarion. Also included are 7 Gold Champion Chests for each and an exclusive Skin & Feat Shadowheart!",  # noqa: E501
                "developer": "Codename Entertainment",
            },
            {
                "id": "warframe_holiday_sale_2023",
                "game_name": "Warframe - Holiday Sale 2023",
                "game_url": "https://store.epicgames.com/en-US/p/warframe",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/warframe_holiday_sale_2023.jpg",
                "description": "Come celebrate the Epic Games Holiday Sale with us and claim the Atterax Weapon, a 7-Day Credit Booster and 7-Day Affinity Booster for free!\nPlayers who launch and log in to WARFRAME on Epic Games Store during the promotional period will receive an inbox message with free content upon login into the game. ",  # noqa: E501
                "developer": "Digital Extremes",
            },
            {
                "id": "honkai_impact_holiday_sale_2023",
                "game_name": "Honkai Impact - Holiday Sale 2023",
                "game_url": "https://store.epicgames.com/en-US/p/honkai-impact-3rd",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/honkai_impact_holiday_sale_2023.jpg",
                "description": "Celebrate the Epic Games Holiday Sale and get 500 Asterites and 100,000 Coins for free!\nPlayers who log in to Honkai Impact 3rd on Epic Games Store during the event period will receive the bundle via an in-game mail within one week.",  # noqa: E501
                "developer": "miHoYo Limited",
            },
            {
                "id": "synced_holiday_sale_2023",
                "game_name": "SYNCED: Winterfest Bundle",
                "game_url": "https://store.epicgames.com/en-US/p/synced--winterfest-bundle",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/synced_holiday_sale_2023.jpg",
                "description": "Unlock this Bundle of SYNCED to obtain new Runner and weapon skins, and embrace fresh challenges in the new season - Lambent Dawn.",  # noqa: E501
                "developer": "NExT Studios",
            },
            {
                "id": "world_of_warships_holiday_sale_2023",
                "game_name": "World of Warships — Frosty Celebration Pack",
                "game_url": "https://store.epicgames.com/en-US/p/world-of-warships--frosty-celebration-pack",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/world_of_warships_holiday_sale_2023.jpg",
                "description": "Embrace the magic of the winter holidays with this free DLC featuring cruiser Ning Hai and the enchanting allure of even more Premium ships that could drop from five festive Santa's Gift containers.",  # noqa: E501
                "developer": "Wargaming",
            },
            {
                "id": "eve_online_superluminal_pack",
                "game_name": "EVE Online - Superluminal Pack",
                "game_url": "https://store.epicgames.com/en-US/p/eve-online--superluminal-pack",
                "start_date": datetime.datetime(year=2023, month=12, day=13, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=1, day=10, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/eve_online_superluminal_pack.jpg",
                "description": "The Superluminal Pack is a limited-time-only FREE giveaway exclusive to Epic! It contains Semiotique Superluminal SKINs for the Heron, Magnate, Imicus, and Probe as well as unique Superluminal clothing!",  # noqa: E501
                "developer": "CCP Games",
            },
            {
                "id": "epic_mega_sale_2024",
                "game_name": "Epic Games MEGA Sale 2024",
                "game_url": "https://store.epicgames.com/en-US/free-games",
                "start_date": datetime.datetime(year=2024, month=5, day=16, hour=18, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=6, day=12, hour=0, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/epic_mega_sale_2024.jpg",
                "description": "Free Epic stuff:\n- [Disney Speedstorm Monochromatic Pack - Racer Stitch](https://store.epicgames.com/en-US/p/disney-speedstorm--racer-stitch)\n- [Genshin Impact MEGA Sale Bundle](https://store.epicgames.com/en-US/p/genshin-impact--mega-sale-bundle)\n- [Honkai: Star Rail MEGA Sale Bundle](https://store.epicgames.com/en-US/p/honkai-star-rail--epic-mega-sale-event-bundle)\n- [Fortnite Overclocked Combo Pack](https://store.epicgames.com/en-US/p/fortnite--overclocked-combo-pack)\n- [Fall Guys - Soda Crown](https://store.epicgames.com/en-US/p/fall-guys--soda-crown)\n- [1 Month of Discord Nitro](https://store.epicgames.com/en-US/p/discord--discord-nitro)\n- [Dauntless Golden Drake's Eye Bundle](https://store.epicgames.com/en-US/p/dauntless--golden-drakes-eye-bundle)\n- [Warframe Pyra Syandana and Fire Color Picker](https://store.epicgames.com/en-US/p/warframe)\n- [Honkai Impact 3rd Bundle](https://store.epicgames.com/en-US/p/honkai-impact-3rd)",  # noqa: E501
                "developer": "Epic Games et al.",
            },
            {
                "id": "wuthering_waves_echo_starter_pack",
                "game_name": "Wuthering Waves - Echo Starter Pack",
                "game_url": "https://store.epicgames.com/en-US/p/wuthering-waves-echo-starter-pack-eae1db",
                "start_date": datetime.datetime(year=2024, month=5, day=23, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "end_date": datetime.datetime(year=2024, month=6, day=23, hour=16, minute=0, second=0, tzinfo=datetime.UTC).isoformat(),
                "image_link": "https://thelovinator1.github.io/discord-free-game-notifier/images/wuthering_waves_echo_starter_pack.jpg",
                "description": "The Echo Starter Pack includes:\n- 1 Incomplete Echo\n- 10 Premium Tuner\n- 5 Advanced Sealed Tube",
                "developer": "KURO GAMES",
            },
        ],
    }

    with Path.open(Path("pages/epic.json"), "w", encoding="utf-8") as file:
        json.dump(free_games, file, indent=4)
        logger.bind(game_name="Epic").info("Created/updated epic.json")


def get_json() -> FreeGamesResponse | None:
    """Gets a json file from the json folder.

    Returns:
        dict: The json file as a dict. If the connection fails, return None.
    """
    json_location: str = "https://thelovinator1.github.io/discord-free-game-notifier/epic.json"

    try:
        json_file: FreeGamesResponse = requests.get(json_location, timeout=30).json()
    except requests.exceptions.ConnectionError:
        logger.bind(game_name="Epic").error("Unable to connect to https://thelovinator1.github.io/discord-free-game-notifier/epic.json")
        return None
    else:
        logger.bind(game_name="Epic").info("Successfully retrieved epic.json")
        return json_file


def scrape_epic_json() -> list[DiscordEmbed]:  # noqa: PLR0914
    """Get the free games from Epic.json.

    Returns:
        list[DiscordEmbed]: A list of embeds containing the free games.
    """
    # List of embeds to return
    list_of_embeds: list[DiscordEmbed] = []

    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "epic.txt"

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Check Epic.json if free games
    epic_json: FreeGamesResponse | None = get_json()
    if not epic_json:
        return list_of_embeds

    # Get the free games from Epic.json
    free_games: list[FreeGame] = epic_json["free_games"]

    for _game in free_games:
        game_id: str = _game["id"]
        game_name: str = _game["game_name"]
        description: str = _game["description"]
        game_url: str = _game["game_url"]
        image_url: str = _game["image_link"]
        start_date: str = _game["start_date"]
        developer: str = _game["developer"]
        unix_start_date: int = int(
            datetime.datetime.fromisoformat(start_date).timestamp(),
        )
        end_date: str = _game["end_date"]
        unix_end_date: int = int(datetime.datetime.fromisoformat(end_date).timestamp())

        # Check if the game has already been posted
        if already_posted(previous_games, game_id):
            continue

        # Check if the game is still free
        current_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
        if unix_end_date < current_time:
            logger.info(f"{game_name} is no longer free")
            continue

        # Create the embed and add it to the list of free games.
        embed = DiscordEmbed(description=description)
        embed.set_author(
            name=f"{game_name}",
            url=game_url,
            icon_url=settings.epic_icon,
        )
        embed.set_image(url=image_url)
        embed.set_timestamp()
        embed.add_embed_field(name="Start", value=f"<t:{unix_start_date}:R>")
        embed.add_embed_field(name="End", value=f"<t:{unix_end_date}:R>")
        embed.set_footer(text=developer)  # pyright: ignore[reportUnknownMemberType]

        with Path.open(previous_games, "a+", encoding="utf-8") as file:
            file.write(f"{game_id}\n")

        list_of_embeds.append(embed)

    return list_of_embeds


if __name__ == "__main__":
    create_json_file()
    for game in scrape_epic_json():
        response: requests.Response = send_embed_webhook(game)
        if not response.ok:
            logger.error(
                f"Error when checking game for Epic (JSON):\n{response.status_code} - {response.reason}: {response.text}",
            )
