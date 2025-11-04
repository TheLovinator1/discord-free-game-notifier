# syntax=docker/dockerfile:1
# check=error=true

# ============================================================================
# Builder Stage: Compile and install Python dependencies
# ============================================================================
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

# Optimize uv behavior: compile Python bytecode and copy (not symlink) files
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Set consistent Python installation directory across builds
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use uv-managed Python versions (ignore system Python)
ENV UV_PYTHON_PREFERENCE=only-managed

# Install the specified Python version
ARG UV_PYTHON_VERSION=3.14
RUN uv python install ${UV_PYTHON_VERSION}

WORKDIR /app

# Copy dependency manifests first for better layer caching
# Docker will reuse this layer if these files haven't changed
COPY --link pyproject.toml /app/pyproject.toml
COPY --link README.md /app/README.md

# Install dependencies without installing the project itself
# Uses cache mount to speed up repeated builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# Copy application source code
COPY --link src/ /app/src/

# Install the project itself along with its dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# ============================================================================
# Runtime Stage: Minimal image with only runtime dependencies
# ============================================================================
FROM python:3.14-slim-bookworm

# Create non-root user for security best practices
RUN set -eux; \
    rm -rf /var/lib/apt/lists/*; \
    useradd --create-home botuser

# Copy only the virtual environment and source code from builder stage
# This keeps the final image small by excluding build tools
COPY --from=builder --link /app/.venv /app/.venv
COPY --from=builder --link /app/src /app/src

# Add virtual environment binaries to PATH so commands work without activation
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user for running the application
USER botuser

WORKDIR /app

# Create directory for persistent data storage (database, cache, etc.)
RUN mkdir -p /home/botuser/.local/share/discord_free_game_notifier/
VOLUME ["/home/botuser/.local/share/discord_free_game_notifier/"]

# Run the Discord bot
CMD ["python", "-m", "discord_free_game_notifier.main"]
