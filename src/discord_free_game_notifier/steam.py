from __future__ import annotations

import html
from typing import Self

import httpx
from discord_webhook import DiscordEmbed
from loguru import logger
from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import field_validator

from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import GameService
from discord_free_game_notifier.webhook import send_embed_webhook

STEAM_URL = "https://store.steampowered.com/search/?maxprice=free&specials=1"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"


class Item(BaseModel):
    name: str
    logo: str

    @property
    def app_id(self) -> int:
        """Extract the Steam app ID from the logo URL."""
        return int(self.logo.split("/apps/")[1].split("/")[0])


class Data(BaseModel):
    desc: str
    items: list[Item]


class Game(BaseModel):
    name: str
    id: int

    @field_validator("name")
    @classmethod
    def unescape_name(cls, v: str) -> str:
        """Ensure Steam game names are unescaped at parse time.

        Args:
            v: Raw name string from API which may contain HTML entities.

        Returns:
            str: Name with HTML entities unescaped.
        """
        return html.unescape(v) if isinstance(v, str) else v


class PriceOverview(BaseModel):
    currency: str
    initial: int
    final: int
    discount_percent: int
    initial_formatted: str
    final_formatted: str


class ReleaseDate(BaseModel):
    coming_soon: bool
    date: str


class AppDetailsData(BaseModel):
    developers: list[str] | None = None
    publishers: list[str] | None = None
    price_overview: PriceOverview | None = None
    release_date: ReleaseDate | None = None
    header_image: str | None = None
    short_description: str | None = None


class AppDetails(BaseModel):
    success: bool
    data: AppDetailsData | None = None


class QuerySummary(BaseModel):
    num_reviews: int
    review_score: int
    review_score_desc: str
    total_positive: int
    total_negative: int
    total_reviews: int


class ReviewsResponse(BaseModel):
    success: int
    query_summary: QuerySummary


class MoreData(BaseModel):
    """A Pydantic model to hold more data about the game."""

    # "Stellar Mess is a 2D point&amp;click adventure game, set somewhere in Argentinean Patagonia. The game is inspired by early classic EGA games of the genre." # noqa: E501
    short_description: str = ""

    # "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1507530/header.jpg?t=1737679003"
    header_image: str | None = None

    # ["Tibba Games"]
    developers: list[str] = []

    # ["Tibba Games"]
    publishers: list[str] = []

    # "4,99€"
    old_price: str = ""

    # "11 Feb, 2022"
    release_date: str = ""

    # "Mixed"
    reviews: str = ""

    @classmethod
    def from_app_details(cls, data: AppDetailsData, game_id: str) -> Self:
        """Create MoreData from AppDetailsData.

        Args:
            data: The parsed app details data
            game_id: The game ID for logging

        Returns:
            MoreData: A new instance with data extracted from AppDetailsData
        """
        instance: Self = cls()

        if data.header_image:
            logger.debug(f"header_image={data.header_image} for {game_id=}")
            instance.header_image = data.header_image

        if data.short_description:
            logger.debug(f"short_description={data.short_description} for {game_id=}")
            instance.short_description = data.short_description

        if data.developers:
            logger.debug(f"developers={data.developers} for {game_id=}")
            instance.developers = data.developers

        if data.publishers:
            logger.debug(f"publishers={data.publishers} for {game_id=}")
            instance.publishers = data.publishers

        if data.price_overview:
            instance.old_price = data.price_overview.initial_formatted

        if data.release_date:
            instance.release_date = data.release_date.date

        return instance


def _process_game(game: Game) -> tuple[DiscordEmbed, str] | None:
    """Process a single game and create its Discord embed.

    Args:
        game: The game to process

    Returns:
        tuple[DiscordEmbed, str] | None: A tuple of (embed, game_name) or None if already posted
    """
    logger.info(f"Checking game: {game.name}")
    if already_posted(game_service=GameService.STEAM, game_name=game.name):
        logger.info(f"Game already posted: {game.name}")
        return None

    embed = DiscordEmbed(color="fcc603")

    embed.set_author(
        name=game.name,
        url=f"https://store.steampowered.com/app/{game.id}/",
        icon_url="https://thelovinator1.github.io/discord-free-game-notifier/images/Steam.png",
    )

    more_data: MoreData = get_more_data(str(game.id))

    header_url: str | None = more_data.header_image
    if not header_url:
        header_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/753/header.jpg"

    embed.set_image(url=header_url)

    if more_data.short_description:
        embed.description = html.unescape(more_data.short_description)

    if more_data.old_price:
        embed.add_embed_field(name="Old Price", value=more_data.old_price)

    if more_data.release_date:
        embed.add_embed_field(name="Release Date", value=more_data.release_date)

    if more_data.reviews:
        embed.add_embed_field(name="Reviews", value=more_data.reviews)

    set_game_footer(more_data, embed)

    logger.debug(f"More data for {game.name}: {more_data}")
    logger.info(f"Posting game: {game.name}")

    return (embed, game.name)


def get_more_data(game_id: str | None) -> MoreData:
    """Get more data about the game.

    Args:
        game_id (str | None): The game ID. If None, return empty data.

    Returns:
        MoreData: A Pydantic model with more data about the game or empty data.
    """
    if not game_id:
        return MoreData()

    logger.debug(f"Getting more data for {game_id=}")

    more_data: MoreData = _fetch_app_details(game_id)
    _fetch_reviews(game_id, more_data)

    return more_data


def _fetch_app_details(game_id: str) -> MoreData:
    """Fetch app details from Steam API.

    Args:
        game_id: The game ID

    Returns:
        MoreData: Populated MoreData instance or empty instance on error
    """
    with httpx.Client(timeout=30) as client:
        appdetails_response: httpx.Response = client.get(
            url=f"https://store.steampowered.com/api/appdetails?appids={game_id}&l=english&filters=basic,short_description,developers,publishers,price_overview,release_date",
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=30,
        )

    if appdetails_response.is_error:
        logger.error(f"Failed to get more data for {game_id=}: {appdetails_response.status_code} - {appdetails_response.reason_phrase}")
        return MoreData()

    try:
        response_data: dict[str, AppDetails] = appdetails_response.json()
        app_details: AppDetails = AppDetails.model_validate(response_data.get(game_id, {}))

        if app_details.success and app_details.data:
            return MoreData.from_app_details(app_details.data, game_id)

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse app details for {game_id=}: {e}")

    return MoreData()


def _fetch_reviews(game_id: str, more_data: MoreData) -> None:
    """Fetch and parse game reviews.

    Args:
        game_id: The game ID
        more_data: The MoreData object to populate
    """
    logger.debug(f"Getting reviews for {game_id=}")

    with httpx.Client(timeout=30) as client:
        reviews_response: httpx.Response = client.get(
            url=f"https://store.steampowered.com/appreviews/{game_id}?json=1&language=all&num_per_page=0&purchase_type=all",
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=30,
        )

    if reviews_response.is_error:
        logger.error(f"Failed to get reviews for {game_id=}: {reviews_response.status_code} - {reviews_response.reason_phrase}")
        return

    try:
        reviews_data: ReviewsResponse = ReviewsResponse.model_validate_json(reviews_response.text)
        if reviews_data.success:
            logger.debug(f"reviews={reviews_data.query_summary.review_score_desc} for {game_id=}")
            more_data.reviews = reviews_data.query_summary.review_score_desc

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse reviews for {game_id=}: {e}")


def get_free_steam_games() -> list[tuple[DiscordEmbed, str]] | None:
    """Go to the Steam store and check for free games and return them.

    Returns:
        list[tuple[DiscordEmbed, str]] | None: A list of tuples containing the Discord embed and the game name. Game name is to track already posted games.
    """  # noqa: E501
    try:
        url = "https://store.steampowered.com/search/results/?maxprice=free&specials=1&category1=994%2C998%2C21&json=1"

        with httpx.Client(timeout=30) as client:
            request: httpx.Response = client.get(url=url, headers={"User-Agent": DEFAULT_USER_AGENT})

        if not request.is_success:
            logger.error(f"Failed to get free Steam games: {request.status_code} - {request.reason_phrase}")
            return None

        parsed: Data = Data.model_validate_json(request.text)
        games: list[Game] = [Game(name=item.name, id=item.app_id) for item in parsed.items]

        found_games: list[tuple[DiscordEmbed, str]] = []

        for game in games:
            result: tuple[DiscordEmbed, str] | None = _process_game(game)
            if result:
                found_games.append(result)

    except (httpx.HTTPError, ValidationError, ValueError, LookupError, TypeError, AttributeError) as e:
        logger.error(f"Error getting free Steam games: {e}")
        return None
    else:
        return found_games


def set_game_footer(more_data: MoreData, embed: DiscordEmbed) -> None:
    """Set the game developer/publisher information in the embed footer.

    Args:
        more_data (MoreData): The dataclass with more data about the game.
        embed (DiscordEmbed): The Discord embed object.
    """
    if not (more_data.developers or more_data.publishers):
        return

    if more_data.developers == more_data.publishers:
        footer: str = f"Developed by {', '.join(more_data.developers)}"
    else:
        developers: str = f"{', '.join(more_data.developers)}" if more_data.developers else ""
        publishers: str = f"{', '.join(more_data.publishers)}" if more_data.publishers else ""

        if developers and publishers:
            footer = f"Developed by {developers} | Published by {publishers}"
        else:
            footer = f"Developed by {developers or publishers}"

    embed.set_footer(text=footer)


def main() -> None:
    """Main function to check for free Steam games and send them to Discord."""
    free_games: list[tuple[DiscordEmbed, str]] | None = get_free_steam_games()
    if free_games:
        for embed, game_name in free_games:
            logger.info(f"Posting game: {game_name}")
            send_embed_webhook(embed=embed, game_id=game_name, game_service=GameService.STEAM)


if __name__ == "__main__":
    main()
