# discord-free-game-notifier

<p align="center">
  <img src="extras/Bot.jpg" title="New free game: Rise of the Tomb Raider"/>
</p>
<p align="center"><sup>Theme is https://github.com/KillYoy/DiscordNight<sup></p>

Send webhook to Discord when a new game releases on Epic, Steam or GOG.

## Docker

There is a docker-compose.yml file in the root of the repository.
You need to add your Discord webhook URL to the `WEBHOOK_URL`
environment variable.

## Usage (GNU/Linux)

- Install [Python](https://www.python.org/) and [Poetry](https://python-poetry.org/docs/master/).
- Download or clone the repository.
- Change directory to the root of the repository.
- Install the dependencies using `poetry install`.
- Run the bot once to create the config file.
    - `poetry run bot`
- Rename .env.example to .env and fill in the values. You can also set the values as environment variables.
- Start the bot for real.
    - `poetry run bot`
- The bot will now check for free games every 30 minutes and send a message to the webhook.

## Need help?

- Email: [tlovinator@gmail.com](mailto:tlovinator@gmail.com)
- Discord: TheLovinator#9276
- Send an issue: [discord-embed/issues](https://github.com/TheLovinator1/discord-free-game-notifier/issues)
