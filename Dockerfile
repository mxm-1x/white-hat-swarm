# White-Hat Command Center — backend + the 4 Band agents in one container.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SPAWN_AGENTS=1

# uv for fast, locked installs
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install deps first (better layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# App code (secrets are NOT copied — see .dockerignore; they come from env)
COPY . .

# Render/!$PORT provides the port; default 8000 locally
CMD ["sh", "-c", "uv run uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
