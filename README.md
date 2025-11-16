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

## Data Storage

- Windows: `%APPDATA%/TheLovinator/discord_free_game_notifier`
- Linux: `~/.local/share/discord_free_game_notifier/`
