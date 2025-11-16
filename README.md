# discord-free-game-notifier

<p align="center">
  <img src="extras/Bot.jpg" title="New free game: Rise of the Tomb Raider"/>
</p>

Discord webhook notifications for free games on Steam, Epic, GOG, and Ubisoft.

## Setup

**Docker:** See [docker-compose.yml](./docker-compose.yml)

Available tags:

- `latest` - Latest build from master branch
- `2.0.0` - Pin to specific version (recommended for stability)
- `2.0` - Pin to minor version (gets patch updates)
- `2` - Pin to major version

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

## Configuration

All settings are configured via environment variables (or `.env` file):

### Required Settings

- `WEBHOOK_URL` - Main Discord webhook URL for all game notifications

### Optional Store-Specific Webhooks

Send notifications to different webhooks based on the game store:

- `STEAM_WEBHOOK` - Discord webhook URL for Steam games
- `EPIC_WEBHOOK` - Discord webhook URL for Epic Games
- `GOG_WEBHOOK` - Discord webhook URL for GOG games
- `UBISOFT_WEBHOOK` - Discord webhook URL for Ubisoft games

### Filter Settings

Control which games you want to be notified about:

- `PLATFORMS` - Comma-separated list of platforms: `pc`, `android`, `ios`
  - Examples:
    - `PLATFORMS=pc` - Only PC games
    - `PLATFORMS=android,ios` - Only mobile games
    - `PLATFORMS=pc,android,ios` or leave empty - All platforms (default)

- `STORES` - Comma-separated list of stores: `steam`, `epic`, `gog`, `ubisoft`
  - Examples:
    - `STORES=steam,epic` - Only Steam and Epic Games
    - `STORES=epic` - Only Epic Games
    - Leave empty - All stores (default)

### Other Settings

- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO

### Example Configuration

```env
# Main webhook (required if no store-specific webhooks are set)
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Optional: Send Steam games to a different channel
STEAM_WEBHOOK=https://discord.com/api/webhooks/STEAM_WEBHOOK_ID/STEAM_WEBHOOK_TOKEN

# Optional: Only check Steam and Epic, only PC games
STORES=steam,epic
PLATFORMS=pc

# Optional: Adjust logging
LOG_LEVEL=INFO
```

## Data Storage

- Windows: `%APPDATA%/TheLovinator/discord_free_game_notifier`
- Linux: `~/.local/share/discord_free_game_notifier/`
