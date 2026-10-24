# syntax=docker/dockerfile:1
# check=error=true

# Builder Stage: Compile and install Python dependencies
FROM ghcr.io/astral-sh/uv:python3.15-trixie-slim AS builder

# Optimize uv behavior: compile Python bytecode and copy (not symlink) files
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies without installing the project itself
# Uses cache mount to speed up repeated builds and bind mounts for files
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --no-install-project --no-dev --frozen

# Copy the project into the image
COPY . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-editable

# Runtime Stage: Minimal image with only runtime dependencies
FROM python:3.15-slim-trixie

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

# Create non-root user for security best practices
RUN RUN useradd --create-home botuser \
    && mkdir -p /home/botuser/.local/share/discord_free_game_notifier \
    && chown -R botuser:botuser /home/botuser/.local/share/discord_free_game_notifier

WORKDIR /app

# Copy the installed virtual environment.
COPY --from=builder --link /app/.venv /app/.venv

# Fail the build if the application cannot be imported.
RUN /app/.venv/bin/python -c "import discord_free_game_notifier.main"

# Switch to non-root user for running the application
USER botuser

VOLUME ["/home/botuser/.local/share/discord_free_game_notifier/"]

# Run the Discord bot
CMD ["python", "-m", "discord_free_game_notifier.main"]
