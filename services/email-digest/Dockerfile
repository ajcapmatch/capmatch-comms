FROM python:3.13-slim

# 1. Setup standard python env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 2. Install uv (using the COPY method is best/fastest)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Copy dependencies (relative to repo root build context)
COPY services/email-digest/pyproject.toml services/email-digest/uv.lock ./

# 4. Create venv and install dependencies
# uv automatically creates .venv in the current directory
RUN uv sync --frozen --no-install-project

# 5. "Activate" the venv for all future commands
# By putting the venv bin directory first in PATH, 'python' now refers to the venv python
ENV PATH="/app/.venv/bin:$PATH"

# 6. Copy service code and shared template artifacts
COPY services/email-digest/ .
COPY packages/email-templates/dist/ packages/email-templates/dist/

# Use uv run to ensure we're using the correct Python environment
CMD ["uv", "run", "python", "main.py"]
