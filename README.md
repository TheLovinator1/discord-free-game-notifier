# discord-free-game-notifier

<p align="center">
  <img src="extras/Bot.jpg" title="New free game: Rise of the Tomb Raider"/>
</p>
<p align="center"><sup>Theme is https://github.com/KillYoy/DiscordNight<sup></p>

Send webhook to Discord when a game goes from paid from free on Steam, Epic, GOG and Ubisoft.

## Docker

There is a docker-compose.yml file in the root of the repository.
Please fill in the values in the .env file and run `docker-compose up -d`.

## Usage (Windows)

- Install [Python](https://www.python.org/downloads/)
  - Add Python to PATH during installation.
- Download or clone the repository.
  - [Download the repository as a zip file](https://github.com/TheLovinator1/discord-free-game-notifier/archive/refs/heads/master.zip) and extract it.
  - `git clone https://github.com/TheLovinator1/discord-free-game-notifier.git` (if you have Git installed)
- Open the extracted folder in File Explorer.
- Shift + Right-click in the folder and select "Open PowerShell window here".
- Set the execution policy to allow running scripts.
  - `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
  - Type `Y` and press Enter.
- Create a virtual environment and activate it.
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
- Install the dependencies.
  - `pip install -r requirements.txt`
- Rename .env.example to .env and fill in the values.
  - `Rename-Item .env.example .env`
  - `notepad .env`
- Start the bot.
  - `python .\discord_free_game_notifier\main.py`
- The bot will now check for free games every 15 minutes and send a message to the webhook.
- Data is stored in `%appdata%\TheLovinator\discord_free_game_notifier`.
- To stop the bot, press `Ctrl + C` in the PowerShell window.

## Usage (GNU/Linux)

- Install [Python](https://www.python.org/)
  - Ubuntu/Debian: `sudo apt install python3 python3-pip`
  - Fedora/RHEL: `sudo dnf install python3 python3-pip`
  - Arch/Manjaro: `sudo pacman -S python python-pip`
- Download or clone the repository.
  - `git clone https://github.com/TheLovinator1/discord-free-game-notifier.git`
  - Or [download the repository as a zip file](https://github.com/TheLovinator1/discord-free-game-notifier/archive/refs/heads/master.zip) and extract it.
- Change directory to the root of the repository.
  - `cd discord-free-game-notifier`
- Create a virtual environment and activate it.
  - `python -m venv .venv`
  - `source .venv/bin/activate`
- Install the dependencies.
  - `pip install -r requirements.txt`
  - Or `poetry install` if you have [Poetry](https://python-poetry.org/) installed.
- Rename .env.example to .env and fill in the values.
  - `mv .env.example .env`
  - `nano .env`
- Start the bot.
  - `python ./discord_free_game_notifier/main.py`
  - Or `poetry run bot` if you used Poetry.
- The bot will now check for free games every 15 minutes and send a message to the webhook.
- Data is stored in `~/.local/share/discord_free_game_notifier/`.
