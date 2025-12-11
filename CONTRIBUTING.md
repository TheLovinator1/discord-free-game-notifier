# Contributing

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

## Testing Embeds in Discord

You can test and preview Discord embeds from JSON files without waiting for scheduled checks:

```bash
# Test all Epic Games embeds
uv run python -m discord_free_game_notifier.test_embeds epic

# Test specific Steam game (index 0 = first game)
uv run python -m discord_free_game_notifier.test_embeds steam 0

# Test all Epic Mobile games
uv run python -m discord_free_game_notifier.test_embeds epic_mobile

# Test all services at once
uv run python -m discord_free_game_notifier.test_embeds all
```

### Available VS Code Tasks

- `[Test Embeds] Epic (all)` - Send all Epic Games embeds to Discord
- `[Test Embeds] Steam (all)` - Send all Steam embeds to Discord
- `[Test Embeds] Epic Mobile (all)` - Send all Epic Mobile embeds to Discord
- `[Test Embeds] All` - Send all embeds from all services

Usage: Run these tasks from VS Code's Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → "Run Task"

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
