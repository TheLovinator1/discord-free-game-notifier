FROM python:3.12-slim as builder

# Create user so we don't run as root.
RUN useradd --create-home botuser

# Change to the user we created.
USER botuser

# Change directory to where we will run the bot.
WORKDIR /app

# Add the requirements file to the container.
ADD requirements.txt /app/

# Install the Python requirements
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Add main.py and settings.py to the container.
ADD --chown=botuser:botuser discord_free_game_notifier /app/discord_free_game_notifier/

RUN mkdir -p /home/botuser/.local/share/discord_free_game_notifier/

VOLUME ["/home/botuser/.local/share/discord_free_game_notifier/"]

ENV PYTHONPATH "${PYTHONPATH}:/app/discord_free_game_notifier"
CMD ["python", "discord_free_game_notifier/main.py"]
