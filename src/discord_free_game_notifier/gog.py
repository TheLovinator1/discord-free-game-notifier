import httpx
from bs4 import BeautifulSoup
from bs4 import Tag
from discord_webhook import DiscordEmbed
from loguru import logger
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic import ValidationError

from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import GameService
from discord_free_game_notifier.webhook import send_embed_webhook


class GOGGame(BaseModel):
    """Structure for a single GOG free game."""

    id: str = Field(..., max_length=200)
    game_name: str = Field(..., max_length=200)
    game_url: HttpUrl
    image_url: HttpUrl | None = None


def create_embed(
    game: GOGGame,
    *,
    no_claim: bool = False,
) -> DiscordEmbed:
    """Create the embed that we will send to Discord.

    Args:
        game: The GOG game data.
        no_claim: Don't use https://www.gog.com/giveaway/claim

    Returns:
        DiscordEmbed: The embed we will send to Discord.
    """
    game_url = str(game.game_url)

    description = (
        f"[Click here to claim {game.game_name}!](https://www.gog.com/giveaway/claim)\n"
        "[Click here to unsubscribe from emails!]("
        "https://www.gog.com/en/account/settings/subscriptions)"
    )

    if no_claim:
        description = (
            f"[Click here to claim {game.game_name}!]({game_url})\n"
            "[Click here to unsubscribe from emails!]("
            "https://www.gog.com/en/account/settings/subscriptions)"
        )

    embed = DiscordEmbed(description=description)
    embed.set_author(
        name=game.game_name,
        url=game_url,
        icon_url="https://thelovinator1.github.io/discord-free-game-notifier/images/GOG.png",
    )

    if game.image_url:
        image_url_str = str(game.image_url).removesuffix(",")
        if image_url_str.startswith("//"):
            image_url_str = f"https:{image_url_str}"
        embed.set_image(url=image_url_str)

    return embed


def _process_game_child(child: Tag) -> tuple[DiscordEmbed, str] | None:
    """Process a single game child element from the store.

    Args:
        child: The child Tag element to process.

    Returns:
        tuple[DiscordEmbed, str] | None: Tuple containing embed and game ID, or None if processing fails.
    """
    # Game name
    game_class: Tag | None = child.find("div", {"selenium-id": "productTileGameTitle"})
    if game_class is None or "title" not in game_class.attrs:
        return None

    game_name = str(game_class["title"])
    game_id: str = game_name.lower().replace(" ", "_")

    if already_posted(game_service=GameService.GOG, game_name=game_id):
        return None

    logger.info(f"Game name: {game_name}")

    # Game URL
    anchor_tag: Tag | None = child.find("a", {"class": "product-tile--grid"})
    if anchor_tag and hasattr(anchor_tag, "attrs") and "href" in anchor_tag.attrs:
        game_url = str(anchor_tag["href"])
    else:
        game_url = "https://www.gog.com/"
        logger.warning(f"No game URL found for {game_name}, using fallback: {game_url}")

    logger.info(f"Game URL: {game_url}")

    # Game image
    image_url = None
    image_url_class: Tag | None = child.find("source", attrs={"srcset": True})
    if image_url_class and hasattr(image_url_class, "attrs"):
        images: list[str] = str(image_url_class.attrs.get("srcset", "")).strip().split()
        if images:
            image_url: HttpUrl | None = HttpUrl(images[0]) if images[0] else None
            logger.info(f"Image URL: {image_url}")

    gog_game = GOGGame(id=game_id, game_name=game_name, game_url=HttpUrl(game_url), image_url=image_url)

    embed: DiscordEmbed = create_embed(game=gog_game, no_claim=True)
    return (embed, game_id)


def get_free_gog_game_from_store() -> list[tuple[DiscordEmbed, str]]:
    """Check if free GOG game from games store.

    Returns:
        list[tuple[DiscordEmbed, str]]: List of tuples containing embeds and game IDs for free GOG games.
    """
    try:
        with httpx.Client(timeout=30) as client:
            response: httpx.Response = client.get(
                "https://www.gog.com/en/games?priceRange=0,0&discounted=true",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"},
            )
        soup = BeautifulSoup(response.text, "html.parser")

        games: Tag | None = soup.find("div", {"selenium-id": "paginatedProductsGrid"})

        if games is None:
            logger.debug("No free games found")
            return []

        if not hasattr(games, "children"):
            logger.debug("No free games found")
            return []

        free_games: list[tuple[DiscordEmbed, str]] = []

        # Process each child game element
        for child in games.children:
            if not isinstance(child, Tag):
                continue

            result: tuple[DiscordEmbed, str] | None = _process_game_child(child)
            if result:
                free_games.append(result)

    except (httpx.HTTPError, ValidationError, ValueError, LookupError, AttributeError, TypeError) as e:
        logger.error(f"Error getting free GOG games from store: {e}")
        return []
    else:
        return free_games


def get_giveaway_link(giveaway: Tag | None, game_name: str) -> str:
    """Get the giveaway link from the GOG giveaway.

    Args:
        giveaway: The giveaway tag.
        game_name: The game name.

    Returns:
        str: The giveaway link. Defaults to https://www.gog.com/ if not found.
    """
    if not giveaway:
        logger.error("No giveaway found on GOG for {}", giveaway)
        return "https://www.gog.com/"

    gog_giveaway_link = giveaway.find("a", {"selenium-id": "giveawayOverlayLink"})
    if not hasattr(gog_giveaway_link, "attrs"):
        logger.error("No giveaway link found on GOG for {} because it's doesn't have 'attrs'", giveaway)
        return "https://www.gog.com/"

    # Only allow Tag
    if not isinstance(gog_giveaway_link, Tag):
        logger.error("No giveaway link found on GOG for {} because it's not a 'Tag'", giveaway)
        return "https://www.gog.com/"

    giveaway_link = str(gog_giveaway_link.attrs.get("href", "https://www.gog.com/"))
    logger.info(f"Giveaway link: {giveaway_link}")
    return giveaway_link


def get_game_image(giveaway: BeautifulSoup, game_name: str) -> str:
    """Get the game image from the GOG giveaway.

    Args:
        giveaway: The giveaway tag.
        game_name: The game name.

    Returns:
        str: The game image URL. Defaults to a placeholder image if not found.
    """
    default_image = "https://images.gog.com/86843ada19050958a1aecf7de9c7403876f74d53230a5a96d7e615c1348ba6a9.webp"

    # Game image
    image_url_class = giveaway.find("source", attrs={"srcset": True})

    # If no image URL, return an empty list
    if image_url_class is None:
        logger.error("No image URL found on GOG for {}", giveaway)
        return default_image

    # Check if image_url_class has attrs
    if not hasattr(image_url_class, "attrs"):
        logger.error("No attrs found on GOG for {}", giveaway)
        return default_image

    images = str(image_url_class.attrs["srcset"]).strip().split()
    image_url = images[0]

    if not image_url:
        logger.error("No image URL found on GOG for {}", giveaway)
        return default_image

    logger.info(f"Image URL: {image_url}")

    return image_url


def get_game_name(giveaway_soup: BeautifulSoup, giveaway: Tag | None) -> str:
    """Get the game name from the GOG giveaway.

    Args:
        giveaway_soup: The giveaway tag.
        giveaway: The giveaway tag.

    Returns:
        str: The game name. Defaults to "GOG Giveaway" if not found.
    """
    img_tag = giveaway_soup.find("img", alt=True)
    if not hasattr(img_tag, "attrs"):
        logger.error("No img tag found on GOG for {}", giveaway)
        return "GOG Giveaway"

    # Extract the game name from the alt attribute
    if img_tag and isinstance(img_tag, Tag):
        game_name_alt = img_tag["alt"]
        if isinstance(game_name_alt, str) and game_name_alt:
            game_name = game_name_alt.replace(" giveaway", "") if img_tag else "Game name not found"
        if isinstance(game_name_alt, list) and game_name_alt:
            game_name = game_name_alt[0].replace(" giveaway", "") if img_tag else "Game name not found"
            logger.warning("was a list of strings so could be wrong?")
    else:
        game_name = "GOG Giveaway"
        logger.error("No img tag found on GOG for {}", img_tag)

    return game_name


def get_free_gog_game() -> tuple[DiscordEmbed, str] | None:
    """Check if free GOG game.

    Returns:
        tuple[DiscordEmbed, str] | None: Tuple containing embed and game ID, or None if no game found.
    """
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                "https://www.gog.com/",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"},
            )

        soup = BeautifulSoup(response.text, "html.parser")
        giveaway = soup.find("giveaway")
        giveaway_soup = BeautifulSoup(str(giveaway), "html.parser")

        if giveaway is None:
            return None

        # Get the game name
        game_name = get_game_name(giveaway_soup=giveaway_soup, giveaway=giveaway)
        game_id = game_name.lower().replace(" ", "_")

        if already_posted(game_service=GameService.GOG, game_name=game_id):
            return None

        giveaway_link = get_giveaway_link(giveaway=giveaway, game_name=game_name)
        image_url_str = get_game_image(giveaway=giveaway_soup, game_name=game_name)

        # Convert image URL to HttpUrl if valid
        image_url = HttpUrl(image_url_str) if image_url_str else None

        gog_game = GOGGame(
            id=game_id,
            game_name=game_name,
            game_url=HttpUrl(giveaway_link),
            image_url=image_url,
        )

        # Create the embed and add it to the list of free games.
        embed: DiscordEmbed = create_embed(game=gog_game)

    except (httpx.HTTPError, ValidationError, ValueError, LookupError, AttributeError, TypeError) as e:
        logger.error(f"Error getting free GOG game: {e}")
        return None
    else:
        return (embed, game_id)


def main() -> None:
    """Entry point to check and send GOG giveaways."""
    if gog_result := get_free_gog_game():
        embed, game_id = gog_result
        send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.GOG)

    for embed, game_id in get_free_gog_game_from_store():
        send_embed_webhook(embed=embed, game_id=game_id, game_service=GameService.GOG)


if __name__ == "__main__":
    main()
