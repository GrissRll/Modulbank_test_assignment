FROM python:3.14-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --frozen \
    --no-install-project


FROM base AS development

COPY . .


CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--reload"]


FROM base AS production

COPY . .

RUN uv sync \
    --frozen \
    --no-dev \
    --no-editable

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
