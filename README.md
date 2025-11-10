# discord-free-game-notifier

<p align="center">
  <img src="extras/Bot.jpg" title="New free game: Rise of the Tomb Raider"/>
</p>

Discord webhook notifications for free games on Steam, Epic, GOG, and Ubisoft.

## Architecture Overview

- Bot runs a scheduler at xx:01, xx:16, xx:31, xx:46 every hour to check for new free games.
- Steps starting with Scrape steps hit live store APIs/HTML to discover giveaways (e.g., Epic API, Steam store, GOG homepage).
- Check steps read small curated JSON files under `pages/` (published on GitHub Pages) as a source for deals that scrapers can't find.
- `steam_json.py` and `epic_json.py` creates/updates these files with data from the Python files; the `*_json_check.py` modules consume them during the scheduler run.
- Both sources feed the same pipeline; deduping happens via the "Already posted?" check using the saved game IDs/names.

### Main bot workflow

```mermaid
flowchart TD
    A[Start] --> B[Load environment .env]
    B --> C{Any webhooks configured?}
    C -->|No| D[Exit]
    C -->|Yes| E[Initialize settings]
    E --> F[Start 15-min scheduler]
    F --> G[Run check_free_games]
    G --> H1[Scrape Epic Games API]
    G --> H2[Scrape Epic JSON]
    G --> H3[Check Epic iOS/Android JSON]
    G --> H4[Scrape Steam store]
    G --> H5[Check Steam JSON]
    G --> H6[Scrape GOG store]
    G --> H7[Scrape GOG homepage for giveaway]
    G --> H8[Check Ubisoft JSON]
    H1 --> I[Process found free games]
    H2 --> I
    H3 --> I
    H4 --> I
    H5 --> I
    H6 --> I
    H7 --> I
    H8 --> I
    I --> J{Already posted?}
    J -->|Yes| K[Skip]
    J -->|No| L[Send via webhook]
    L --> M[Save game ID or name to game_name.txt file]
    M --> F
```

## Setup

**Docker:** See [docker-compose.yml](./docker-compose.yml)

**Direct:**

```bash
# Install uv
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure: Copy .env.example to .env and set WEBHOOK_URL

# Run (checks at :01, :16, :31, :46 each hour)
uv run python -m discord_free_game_notifier.main
```

## Manual Checking

```bash
# Check stores directly
uv run python -m discord_free_game_notifier.{steam,epic,gog,ubisoft}

# Check JSON files from /pages
uv run python -m discord_free_game_notifier.{steam,epic}_json_check
```

## Generate JSON

For games not found by scraping, modify `create_json_file()` in:

- [steam_json.py](src/discord_free_game_notifier/steam_json.py)
- [epic_json.py](src/discord_free_game_notifier/epic_json.py)

Then run:

```bash
uv run python -m discord_free_game_notifier.{steam,epic}_json
```

## Data Storage

- Windows: `%APPDATA%/TheLovinator/discord_free_game_notifier`
- Linux: `~/.local/share/discord_free_game_notifier/`

## Notes

- VS Code tasks available: `Ctrl+Shift+P` → "Tasks: Run Task"
- JSON files hosted via GitHub Pages: <https://thelovinator1.github.io/discord-free-game-notifier/>
