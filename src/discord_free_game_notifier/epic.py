from __future__ import annotations

import calendar
import datetime
import html
import time

import httpx
import pytz
from discord_webhook import DiscordEmbed
from loguru import logger
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from requests.utils import requote_uri

from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.utils import already_posted_upcoming
from discord_free_game_notifier.webhook import GameService
from discord_free_game_notifier.webhook import send_embed_webhook
from discord_free_game_notifier.webhook import send_text_webhook


class KeyImage(BaseModel):
    """Structure for game key images."""

    type: str
    url: str


class Seller(BaseModel):
    """Structure for game seller information."""

    id: str
    name: str


class Category(BaseModel):
    """Structure for game categories."""

    path: str


class OfferMapping(BaseModel):
    """Structure for offer mappings."""

    pageSlug: str | None = None
    pageType: str | None = None


class CatalogNsMapping(BaseModel):
    """Structure for catalog namespace mappings."""

    pageSlug: str | None = None
    pageType: str | None = None


class CatalogNs(BaseModel):
    """Structure for catalog namespace container."""

    mappings: list[CatalogNsMapping] | None = None


class DiscountSetting(BaseModel):
    """Structure for discount settings."""

    discountType: str
    discountPercentage: int


class PromotionalOffer(BaseModel):
    """Structure for a single promotional offer."""

    startDate: str | None = None
    endDate: str | None = None
    discountSetting: DiscountSetting | None = None


class PromotionalOfferGroup(BaseModel):
    """Structure for a group of promotional offers."""

    promotionalOffers: list[PromotionalOffer] = Field(default_factory=list)


class Promotions(BaseModel):
    """Structure for game promotions."""

    promotionalOffers: list[PromotionalOfferGroup] = Field(default_factory=list)
    upcomingPromotionalOffers: list[PromotionalOfferGroup] = Field(default_factory=list)


class TotalPrice(BaseModel):
    """Structure for total price information."""

    discountPrice: int
    originalPrice: int
    voucherDiscount: int
    discount: int
    currencyCode: str


class Price(BaseModel):
    """Structure for price information."""

    totalPrice: TotalPrice


class EpicGameElement(BaseModel):
    """Structure for a single game element from Epic API."""

    title: str
    id: str
    namespace: str | None = None
    description: str | None = None
    effectiveDate: str | None = None
    offerType: str | None = None
    expiryDate: str | None = None
    viewableDate: str | None = None
    status: str
    isCodeRedemptionOnly: bool | None = None
    keyImages: list[KeyImage] = Field(default_factory=list)
    seller: Seller | None = None
    productSlug: str | None = None
    urlSlug: str | None = None
    url: str | None = None
    categories: list[Category] = Field(default_factory=list)
    offerMappings: list[OfferMapping] | None = None
    catalogNs: CatalogNs | None = None
    price: Price
    promotions: Promotions | None = None

    @field_validator("title")
    @classmethod
    def unescape_title(cls, v: str) -> str:
        """Ensure titles are human-readable.

        Args:
            v: Raw title string, possibly with HTML entities.

        Returns:
            str: Title with HTML entities unescaped.
        """
        return html.unescape(v) if isinstance(v, str) else v

    @field_validator("productSlug")
    @classmethod
    def validate_product_slug(cls, v: str | None) -> str | None:
        """Validate product slug to handle empty strings and '[]' values.

        Args:
            v: The product slug value.

        Returns:
            None if value is empty, '[]', or None, otherwise returns the value.
        """
        if not v or v == "[]":
            return None
        return v


class SearchStore(BaseModel):
    """Structure for search store data."""

    elements: list[EpicGameElement]


class Catalog(BaseModel):
    """Structure for catalog data."""

    searchStore: SearchStore


class DataWrapper(BaseModel):
    """Structure for the data wrapper."""

    Catalog: Catalog


class EpicGamesResponse(BaseModel):
    """Structure for the Epic Games API response."""

    data: DataWrapper


def _parse_iso_utc_to_unix(ts: str) -> int:
    """Parse an Epic ISO timestamp (Z suffix) into a UTC unix timestamp.

    Args:
        ts: Timestamp string like "2022-04-07T15:00:00.000Z".

    Returns:
        int: Unix timestamp (seconds since epoch, UTC).
    """
    # Use calendar.timegm to avoid local timezone conversion issues.
    return int(calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")))


def promotion_start(game: EpicGameElement) -> int:
    """Get the earliest start date of a game's promotion (current or upcoming).

    Epic frequently places free-game promos either under promotionalOffers (active)
    or upcomingPromotionalOffers (scheduled). We consider the earliest available
    start across both, preferring active when present.

    Args:
        game: The game element model.

    Returns:
        int: Start date as Unix timestamp, or 0 if unavailable.
    """
    if not game.promotions:
        return 0

    start_candidates: list[int] = []

    # Active promotions
    for group in game.promotions.promotionalOffers:
        for offer in group.promotionalOffers:
            if offer.startDate:
                try:
                    start_candidates.append(_parse_iso_utc_to_unix(offer.startDate))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"{game.title}: Unable to parse startDate '{offer.startDate}': {e}")

    # Upcoming promotions
    for group in game.promotions.upcomingPromotionalOffers:
        for offer in group.promotionalOffers:
            if offer.startDate:
                try:
                    start_candidates.append(_parse_iso_utc_to_unix(offer.startDate))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"{game.title}: Unable to parse upcoming startDate '{offer.startDate}': {e}")

    start_date: int = min(start_candidates) if start_candidates else 0
    logger.info(f"{game.title}: Starts in: {start_date} ({datetime.datetime.fromtimestamp(start_date, tz=pytz.UTC)})")
    return start_date


def promotion_end(game: EpicGameElement) -> int:
    """Get the latest end date of a game's promotion (current or upcoming).

    We consider both active and upcoming promotional groups. For active promos
    we typically want the soonest end; for simplicity, pick the max end date
    across all available entries which ensures coverage in bundles.

    Args:
        game: The game element model.

    Returns:
        int: End date as Unix timestamp, or 0 if unavailable.
    """
    if not game.promotions:
        return 0

    end_candidates: list[int] = []

    # Active promotions
    for group in game.promotions.promotionalOffers:
        for offer in group.promotionalOffers:
            if offer.endDate:
                try:
                    end_candidates.append(_parse_iso_utc_to_unix(offer.endDate))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"{game.title}: Unable to parse endDate '{offer.endDate}': {e}")

    # Upcoming promotions
    for group in game.promotions.upcomingPromotionalOffers:
        for offer in group.promotionalOffers:
            if offer.endDate:
                try:
                    end_candidates.append(_parse_iso_utc_to_unix(offer.endDate))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"{game.title}: Unable to parse upcoming endDate '{offer.endDate}': {e}")

    end_date: int = max(end_candidates) if end_candidates else 0
    logger.info(f"{game.title}: Ends in: {end_date}")
    return end_date


def game_image(game: EpicGameElement) -> str:
    """Get an image URL for the game.

    Args:
        game: The free game element to get the image of.

    Returns:
        str: Returns the image URL of the game.
    """
    image_url: str = ""
    for image in game.keyImages:
        if image.type in {"DieselStoreFrontWide", "Thumbnail"}:
            image_url = str(image.url)
            logger.debug(f"{game.title}: Found image URL: {image_url} (type: {image.type})")

    # This fixes https://github.com/TheLovinator1/discord-free-game-notifier/issues/70
    if not image_url:
        for image in game.keyImages:
            if image.type == "OfferImageWide":
                image_url = str(image.url)
                logger.debug(f"{game.title}: Found image URL: {image_url} (type: {image.type})")

    logger.info(f"{game.title}: Image URL: {requote_uri(image_url)}")
    return requote_uri(image_url)


def game_url(game: EpicGameElement) -> str:
    """If you click the game name, you'll be taken to the game's page on Epic.

    Args:
        game: The game element model.

    Returns:
        str: Returns the URL of the game.
    """
    url: str = "https://store.epicgames.com/"
    if product_slug := game.productSlug:
        url = f"https://www.epicgames.com/en-US/p/{product_slug}"
    else:
        logger.debug(f"{game.title}: Product slug is empty")
        if game.offerMappings:
            for offer in game.offerMappings:
                if offer.pageSlug:
                    page_slug: str = offer.pageSlug
                    url = f"https://www.epicgames.com/en-US/p/{page_slug}"
                    logger.debug(f"{game.title}: Found page slug")

        # Fallback to urlSlug if offerMappings are missing or unavailable
        elif game.urlSlug:
            url = f"https://www.epicgames.com/en-US/p/{game.urlSlug}"
            logger.debug(f"{game.title}: Using urlSlug as fallback")

        # Second fallback: catalogNs.mappings
        elif game.catalogNs and game.catalogNs.mappings:
            for mapping in game.catalogNs.mappings:
                if mapping.pageSlug:
                    url = f"https://www.epicgames.com/en-US/p/{mapping.pageSlug}"
                    logger.debug(f"{game.title}: Using catalogNs.mappings pageSlug")
                    break

    logger.info(f"{game.title}: URL: {requote_uri(url)}")
    return requote_uri(url)


def get_response() -> EpicGamesResponse | None:
    """Get the response from Epic and parse it with Pydantic.

    Returns:
        EpicGamesResponse: The parsed Epic Games API response, or None if error.
    """
    with httpx.Client(timeout=30, transport=httpx.HTTPTransport(retries=5)) as client:
        try:
            response: httpx.Response = client.get("https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions")
            logger.debug(f"Response: {response.status_code} - {response.reason_phrase}")

            if response.is_error:
                logger.error(f"Error fetching Epic free games: {response.status_code} - {response.reason_phrase}")
                return None

            return EpicGamesResponse.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"Error parsing Epic Games API response: {e}")
            return None


def if_mystery_game(game: EpicGameElement) -> bool:
    """Check if the game is a mystery game.

    Mystery games are not free games, but games that are coming soon.

    Args:
        game: The game element model.

    Returns:
        bool: True if game is a mystery game.
    """
    if game.title == "Mystery Game":
        logger.info(f"{game.title}: Mystery game, skipping")
        return True
    return False


def get_free_epic_games() -> list[tuple[DiscordEmbed | str, str, bool]] | None:  # noqa: C901, PLR0912, PLR0915
    """Get the free games from Epic.

    Returns:
        list[tuple[DiscordEmbed | str, str, bool]] | None:
            List of tuples containing (embed/message, game_id, is_upcoming), or None if error.
    """
    response: EpicGamesResponse | None = get_response()
    if not response:
        return None

    notified_games: list[tuple[DiscordEmbed | str, str, bool]] = []
    unique_game_ids: set[str] = set()

    curr_dt: datetime.datetime = datetime.datetime.now(tz=pytz.UTC)
    current_time: int = round(curr_dt.timestamp())

    for game in response.data.Catalog.searchStore.elements:
        logger.info(f"Checking game: {game.title}")
        game_title: str = game.title

        if game_title in unique_game_ids:
            logger.debug(f"{game.title}: Already processed in this run, skipping.")
            continue

        if if_mystery_game(game):
            continue

        start_time: int = promotion_start(game)

        # Determine if the game is currently free or upcoming
        is_currently_free: bool = False
        is_upcoming: bool = False

        # Check if game is currently free
        is_price_free: bool = game.price.totalPrice.discountPrice == 0 and game.price.totalPrice.originalPrice > 0
        is_started: bool = start_time == 0 or start_time <= current_time
        if is_price_free and is_started:
            logger.info(f"{game.title}: Identified as currently free based on price.")
            is_currently_free = True

        # Check promotions
        if not is_currently_free and game.promotions:
            all_offers: list[PromotionalOffer] = []
            for group in game.promotions.promotionalOffers:
                all_offers.extend(group.promotionalOffers)
            for group in game.promotions.upcomingPromotionalOffers:
                all_offers.extend(group.promotionalOffers)

            for offer in all_offers:
                if offer.discountSetting and offer.discountSetting.discountPercentage == 0:
                    # Check if this is an active or upcoming promotion
                    offer_start: int = _parse_iso_utc_to_unix(offer.startDate) if offer.startDate else 0
                    if offer_start > current_time:
                        logger.info(f"{game.title}: Identified as upcoming free game.")
                        is_upcoming = True
                    else:
                        logger.info(f"{game.title}: Identified as currently free based on promotion.")
                        is_currently_free = True
                    break

        if is_currently_free:
            # Check if already posted as free game
            if already_posted(game_service=GameService.EPIC, game_name=game_title):
                continue

            if embed := create_embed(game):
                notified_games.append((embed, game_title, False))
                unique_game_ids.add(game_title)
        elif is_upcoming:
            # Check if already posted as upcoming
            if already_posted_upcoming(game_service=GameService.EPIC, game_name=game_title):
                continue

            # Create plain text message for upcoming game
            url: str = game_url(game)
            url = url.removesuffix("/home")

            message: str = (
                f"🎮 **Upcoming Free Game on Epic Games**\n[{game.title}](<{url}>) will be free <t:{start_time}:R> (on <t:{start_time}:F>)"
            )
            notified_games.append((message, game_title, True))
            unique_game_ids.add(game_title)
        else:
            logger.info(f"{game.title}: Not a free or upcoming promotion, skipping.")

    return notified_games


def create_embed(game: EpicGameElement) -> DiscordEmbed | None:
    """Create the embed for the game.

    Args:
        game: The game element model.

    Returns:
        DiscordEmbed | None: The embed with the free game we will send to Discord, or None if game has ended.
    """
    description: str = game.description or "No description found"
    logger.info(f"{game.title}: Description: {description}")
    embed = DiscordEmbed(description=description)
    url: str = game_url(game)
    game_name: str = game.title

    # Jotun had /home appended to the URL and that broke the link
    # Broken: https://www.epicgames.com/en-US/p/jotun/home
    # Fixed: https://www.epicgames.com/en-US/p/jotun
    if url.endswith("/home"):
        logger.debug(f"{game.title}: URL ends with /home")
        url = url[:-5]

    embed.set_author(name=game_name, url=url, icon_url="https://thelovinator1.github.io/discord-free-game-notifier/images/Epic.png")

    curr_dt: datetime.datetime = datetime.datetime.now(tz=pytz.UTC)
    current_time: int = round(curr_dt.timestamp())
    end_time: int = promotion_end(game)
    start_time: int = promotion_start(game)

    if end_time > current_time or (end_time == 0 and start_time != 0):
        if start_time != 0:
            embed.add_embed_field(name="Start", value=f"<t:{start_time}:R>")
        if end_time != 0:
            embed.add_embed_field(name="End", value=f"<t:{end_time}:R>")

        seller: str = game.seller.name if game.seller else "Unknown"

        if seller not in {"Epic Dev Test Account", "Unknown"}:
            logger.info(f"{game.title}: Seller: {seller}")
            embed.set_footer(text=f"{seller}")

        if image_url := game_image(game):
            logger.info(f"{game.title}: Image: {image_url}")
            embed.set_image(url=image_url)

        return embed

    logger.info(f"{game.title}: Game has ended, skipping. End time: {end_time}. Current time: {current_time}")
    return None


def main() -> None:
    """Main function to get free Epic games and send embeds or text messages."""
    free_games: list[tuple[DiscordEmbed | str, str, bool]] | None = get_free_epic_games()
    if free_games:
        for content, game_name, is_upcoming in free_games:
            if is_upcoming:
                if isinstance(content, str):
                    # Send plain text message for upcoming games
                    send_text_webhook(message=content, game_id=game_name, game_service=GameService.EPIC)
            elif isinstance(content, DiscordEmbed):
                # Send embed for currently free games
                send_embed_webhook(embed=content, game_id=game_name, game_service=GameService.EPIC)
            else:
                logger.error(f"Unexpected content type for game name {game_name}, skipping.")


if __name__ == "__main__":
    main()
