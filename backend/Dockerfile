FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir .
# local-embeddings (torch) intentionally NOT installed here — this image
# only runs with LLM_PROVIDER=api, whose adapter embeds via the API.

EXPOSE 8000

# Requires LLM_PROVIDER=api at runtime — the claude_cli adapter needs a
# locally authenticated `claude` CLI, which doesn't exist inside this image.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
