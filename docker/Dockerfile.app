FROM python:3.14-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv
COPY pyproject.toml /app/
RUN uv sync --no-dev --no-install-project
COPY src /app/src
COPY scripts /app/scripts
EXPOSE 8000
ENV PYTHONPATH=/app
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
