# discord-free-game-notifier

<p align="center">
  <img src="extras/Bot.jpg" title="New free game: Rise of the Tomb Raider"/>
</p>
<p align="center"><sup>Theme is https://github.com/KillYoy/DiscordNight<sup></p>

Send webhook to Discord when a new game releases on Epic.

## Usage (GNU/Linux)

- Install [Python](https://www.python.org/) and [Poetry](https://python-poetry.org/docs/master/).
- Download or clone the repository.
- Change directory to the root of the repository.
- Install the dependencies using `poetry install`.
- Run the bot once to create the config file.
  - `poetry run bot`
- Change webhook_url in the config file to the webhook URL you want to use.
  - `nano ~/.config/discord_free_game_notifier/config.conf`
- Add timer to systemd and enable it. Don't forget to change the username.
  - `sudo cp extras/discord-free-game.service /etc/systemd/system/`
  - `sudo cp extras/discord-free-game.timer /etc/systemd/system/`
  - `systemctl enable discord-free-game`
- The bot will now start every hour and if it finds a new game it will send a message to the webhook.

## Need help?

- Email: [tlovinator@gmail.com](mailto:tlovinator@gmail.com)
- Discord: TheLovinator#9276
- Steam: [TheLovinator](https://steamcommunity.com/id/TheLovinator/)
- Send an issue: [discord-embed/issues](https://github.com/TheLovinator1/discord-free-game-notifier/issues)
