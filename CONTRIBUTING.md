# Contributing to discord-free-game-notifier

## Manual Checking

```bash
# Check stores directly
uv run python -m discord_free_game_notifier.steam
uv run python -m discord_free_game_notifier.epic
uv run python -m discord_free_game_notifier.gog
uv run python -m discord_free_game_notifier.ubisoft

# Check JSON files from /pages
uv run python -m discord_free_game_notifier.steam_json_check
uv run python -m discord_free_game_notifier.epic_json_check
```

## Generate JSON

For games not found by scraping, modify `create_json_file()` in:

- [steam_json.py](src/discord_free_game_notifier/steam_json.py)
- [epic_json.py](src/discord_free_game_notifier/epic_json.py)
- [epic_mobile.py](src/discord_free_game_notifier/epic_mobile.py)
- [ubisoft.py](src/discord_free_game_notifier/ubisoft.py)

Then run:

```bash
uv run python -m discord_free_game_notifier.steam_json
uv run python -m discord_free_game_notifier.epic_json
uv run python -m discord_free_game_notifier.epic_mobile
uv run python -m discord_free_game_notifier.ubisoft
```
