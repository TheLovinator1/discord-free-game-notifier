import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed

from discord_free_game_notifier import settings
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.webhook import send_embed_webhook

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"


def get_game_name(banner_title_text: str) -> str:
    """
    Get the game name from the banner title.

    Args:
        banner_title_text: The banner title. We will run a regex to get the game name.

    Returns:
        str: The game name, GOG Giveaway if not found.
    """
    result = re.search(
        r"being with us! Claim (.*?) as a token of our gratitude!",
        banner_title_text,
    )
    if result:
        return result.group(1)
    return "GOG Giveaway"


def create_embed(
        previous_games,
        game_name: str,
        game_url: str,
        image_url: str,
):
    """
    Create the embed that we will send to Discord.

    Args:
        previous_games: The file with previous games in, we will add to it after we sent the webhook.
        game_name: The game name.
        game_url: URL to the game.
        image_url: Game image.

    Returns:
        Embed: The embed we will send to Discord.
    """
    embed = DiscordEmbed(description=f"[Click here to claim {game_name}!](https://www.gog.com/giveaway/claim)\n"
                                     f"[Click here to unsubscribe from emails!]("
                                     f"https://www.gog.com/en/account/settings/subscriptions)")
    embed.set_author(
        name=game_name,
        url=game_url,
        icon_url=settings.gog_icon,
    )

    # Only add the image if it is not empty
    if image_url:
        embed.set_image(url=image_url)

    # Save the game title to the previous games file, so we don't
    # post it again.
    with open(previous_games, "a+", encoding="utf-8") as file:
        file.write(f"{game_name}\n")

    return embed


def get_free_gog_game():
    """Check if free GOG game.

    Returns:
        DiscordEmbed: Embed for the free GOG games.
    """

    # Save previous free games to a file, so we don't post the same games again.
    previous_games: Path = Path(settings.app_dir) / "gog.txt"
    settings.logger.debug(f"Previous games file: {previous_games}")

    # Create the file if it doesn't exist
    if not os.path.exists(previous_games):
        open(previous_games, "w", encoding="utf-8").close()

    request = requests.get("https://www.gog.com/")
    soup = BeautifulSoup(request.text, "html.parser")
    giveaway = soup.find("a", {"id": "giveaway"})

    # If no giveaway, return an empty list
    if giveaway is None:
        return

    # Game name
    banner_title = giveaway.find("span", class_="giveaway-banner__title")
    game_name = get_game_name(banner_title.text)

    # Game URL
    ng_href = giveaway.attrs["ng-href"]
    game_url = f"https://www.gog.com{ng_href}"
    settings.logger.debug(f"\tURL: {game_url}")

    # Game image
    image_url_class = giveaway.find("source", attrs={"srcset": True})
    image_url = image_url_class.attrs["srcset"].strip().split()
    image_url = f"https:{image_url[0]}"
    settings.logger.debug(f"\tImage URL: {image_url}")

    # Check if the game has already been posted
    if already_posted(previous_games, game_name):
        return

    # Create the embed and add it to the list of free games.
    return create_embed(
        previous_games=previous_games,
        game_name=game_name,
        game_url=game_url,
        image_url=image_url,
    )


if __name__ == "__main__":
    # Remember to delete previous games if you are testing
    # It can be found in %appdata%\TheLovinator\discord_free_game_notifier
    gog_embed = get_free_gog_game()
    if gog_embed:
        response = send_embed_webhook(gog_embed)
        if not response.ok:
            print(
                f"Error when checking game for GOG:\n{response.status_code} - {response.reason}: {response.text}")
