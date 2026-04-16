FROM python:3.11-slim

# installa uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# copia manifest e installa dipendenze (layer cacheable)
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

# copia sorgente
COPY app ./app
COPY .env.example .env

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
