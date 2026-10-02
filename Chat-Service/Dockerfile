FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY src ./src

EXPOSE 8000

CMD [".venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
