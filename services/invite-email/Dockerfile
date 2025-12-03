FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependencies from service directory (relative to repo root)
COPY services/invite-email/pyproject.toml .

RUN uv sync --frozen --no-install-project

ENV PATH="/app/.venv/bin:$PATH"

# Copy service code and shared template artifacts
COPY services/invite-email/ .
COPY packages/email-templates/dist/ packages/email-templates/dist/

CMD ["uv", "run", "python", "main.py"]


