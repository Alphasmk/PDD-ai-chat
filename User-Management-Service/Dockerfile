FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_CACHE_DIR=/app/.cache/uv

COPY pyproject.toml uv.lock* ./

RUN uv sync --no-dev --frozen --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app" PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=1 PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r appgroup && useradd -r -g appgroup -m -d /app appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app .

COPY --chown=appuser:appgroup scripts/entry.sh /scripts/entry.sh

RUN chmod +x /scripts/entry.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthcheck')" || exit 1

ENTRYPOINT [ "/scripts/entry.sh" ]

CMD ["uvicorn", "source.main:app", "--host", "0.0.0.0", "--port", "8000"]
