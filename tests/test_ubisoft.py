from pathlib import Path

from discord_free_game_notifier.ubisoft import create_json_file, get_json


def test_create_json_file() -> None:
    """Test that the create_json_file function creates a file."""
    # Remove old file
    if Path("pages/ubisoft.json").exists():
        Path("pages/ubisoft.json").unlink()

    # Create the file
    create_json_file()

    # Check if the file exists
    assert Path("pages/ubisoft.json").exists()


def test_get_json() -> None:
    """Test that the get_json function returns a dict."""
    json = get_json()
    assert isinstance(json, dict)
    assert json["free_games"]

    assert json["free_games"][0]["id"]
    assert json["free_games"][0]["game_name"]
    assert json["free_games"][0]["game_url"]
    assert json["free_games"][0]["start_date"]
    assert json["free_games"][0]["end_date"]
    assert json["free_games"][0]["description"]
    assert json["free_games"][0]["image_link"]
