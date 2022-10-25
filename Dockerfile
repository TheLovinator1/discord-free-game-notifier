FROM python:3.11-slim

# We don't want apt-get to interact with us and we want the default answers to be used for all questions.
ARG DEBIAN_FRONTEND=noninteractive

# Don't generate byte code (.pyc-files).
# These are only needed if we run the python-files several times.
# Docker doesn't keep the data between runs so this adds nothing.
ENV PYTHONDONTWRITEBYTECODE 1

# Force the stdout and stderr streams to be unbuffered.
# Will allow log messages to be immediately dumped instead of being buffered.
# This is useful when the bot crashes before writing messages stuck in the buffer.
ENV PYTHONUNBUFFERED 1

# Update the system and install curl, it is needed for downloading Poetry.
RUN apt-get update && apt-get install curl -y --no-install-recommends

# Create user so we don't run as root.
RUN useradd --create-home botuser

# Change to the user we created.
USER botuser

# Install poetry.
RUN curl -sSL https://install.python-poetry.org | python -

# Add poetry to our path.
ENV PATH="/home/botuser/.local/bin/:${PATH}"

# Copy files from our repository to the container.
ADD --chown=botuser:botuser pyproject.toml poetry.lock README.md LICENSE /home/botuser/discord-free-game-notifier/

# Change directory to where we will run the bot.
WORKDIR /home/botuser/discord-free-game-notifier

# Create config/data directory and install the requirements.
RUN mkdir -p /home/botuser/.local/share/discord_free_game_notifier/ && poetry install --no-interaction --no-ansi --no-dev

# Add main.py and settings.py to the container.
ADD --chown=botuser:botuser discord_free_game_notifier /home/botuser/discord-free-game-notifier/discord_free_game_notifier/

VOLUME ["/home/botuser/.local/share/discord_free_game_notifier/"]

CMD ["poetry", "run", "bot"]
