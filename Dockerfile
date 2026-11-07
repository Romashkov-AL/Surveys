FROM python:3.14-slim AS builder

RUN pip install --no-cache-dir uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    find /app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true


FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app /app

RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
