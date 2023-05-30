import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from discord_webhook import DiscordEmbed
from loguru import logger
from requests.adapters import HTTPAdapter, Retry

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"


def get_game_name(banner_title_text: str) -> str:
    """Get the game name from the banner title.

    Args:
        banner_title_text: The banner title. We will run a regex to get the game name.

    Returns:
        str: The game name, GOG Giveaway if not found.
    """
    if result := re.search(r"being with us! Claim (.*?) as a token of our gratitude!", banner_title_text):
        return result[1]
    return "GOG Giveaway"


def create_embed(
    previous_games: Path,
    game_name: str,
    game_url: str,
    image_url: str,
) -> DiscordEmbed:
    """Create the embed that we will send to Discord.

    Args:
        previous_games: The file with previous games in, we will add to it after we sent the webhook.
        game_name: The game name.
        game_url: URL to the game.
        image_url: Game image.

    Returns:
        Embed: The embed we will send to Discord.
    """
    embed = DiscordEmbed(
        description=(
            f"[Click here to claim {game_name}!](https://www.gog.com/giveaway/claim)\n"
            "[Click here to unsubscribe from emails!]("
            "https://www.gog.com/en/account/settings/subscriptions)"
        ),
    )
    # Set the author and icon
    embed.set_author(name=game_name, url=game_url, icon_url=settings.gog_icon)

    # Only add the image if it is not empty
    if image_url:
        embed.set_image(url=image_url)

    # Save the game title to the previous games file, so we don't
    # post it again.
    with Path.open(previous_games, "a+", encoding="utf-8") as file:
        file.write(f"{game_name}\n")

    return embed


def get_free_gog_game() -> DiscordEmbed | None:
    """Check if free GOG game.

    Returns:
        DiscordEmbed: Embed for the free GOG games.
    """
    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "gog.txt"
    logger.debug(f"Previous games file: {previous_games}")

    # Create the file if it doesn't exist
    if not Path.exists(previous_games):
        with Path.open(previous_games, "w", encoding="utf-8") as file:
            file.write("")

    # Use the same session for all requests to GOG
    session = requests.Session()

    # Retry the request if it fails.
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

    # Use the same session for all requests.
    session.mount("http://", HTTPAdapter(max_retries=retries))

    # Get the Steam store page.
    request: requests.Response = session.get("https://www.gog.com/", headers={"User-Agent": UA}, timeout=30)

    soup = BeautifulSoup(request.text, "html.parser")
    giveaway: Tag | NavigableString | None = soup.find("a", {"id": "giveaway"})

    # If no giveaway, return an empty list
    if giveaway is None:
        return None

    # Game name
    banner_title: Tag | NavigableString | None = giveaway.find("span", class_="giveaway-banner__title")  # type: ignore  # noqa: PGH003, E501

    # If no banner title, return an empty list
    if banner_title is None:
        logger.error("No banner title found on GOG for {}", giveaway)
        return None

    # Check if the game has already been posted
    game_name: str = get_game_name(banner_title.text)
    logger.info(f"Game name: {game_name}")

    # Game URL
    ng_href: str = giveaway.attrs["ng-href"]  # type: ignore  # noqa: PGH003
    game_url: str = f"https://www.gog.com{ng_href}"
    logger.info(f"\tURL: {game_url}")

    # Game image
    image_url_class: Tag | NavigableString | None = giveaway.find("source", attrs={"srcset": True})  # type: ignore  # noqa: PGH003, E501

    # If no image URL, return an empty list
    if image_url_class is None:
        logger.error("No image URL found on GOG for {}", giveaway)
        return None

    # Check if image_url_class has attrs
    if not hasattr(image_url_class, "attrs"):
        logger.error("No attrs found on GOG for {}", giveaway)
        return None

    images: list[str] = image_url_class.attrs["srcset"].strip().split()  # type: ignore  # noqa: PGH003
    image_url: str = f"https:{images[0]}"
    logger.info(f"\tImage URL: {image_url}")

    if already_posted(previous_games, game_name):
        return None

    # Create the embed and add it to the list of free games.
    return create_embed(
        previous_games=previous_games,
        game_name=game_name,
        game_url=game_url,
        image_url=image_url,
    )


if __name__ == "__main__":
    if gog_embed := get_free_gog_game():
        response: requests.Response = send_embed_webhook(gog_embed)
        if not response.ok:
            logger.error(
                "Error when checking game for GOG:\n{} - {}: {}",
                response.status_code,
                response.reason,
                response.text,
            )
