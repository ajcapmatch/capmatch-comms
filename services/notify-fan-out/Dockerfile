FROM python:3.13-slim

# 1. Setup standard python env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 2. Install uv (using the COPY method is best/fastest)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Copy dependencies (relative to repo root build context)
COPY services/notify-fan-out/pyproject.toml ./

# 4. Create venv and install dependencies
# uv automatically creates .venv in the current directory
RUN uv sync --frozen --no-install-project || uv sync --no-install-project

# 5. "Activate" the venv for all future commands
# By putting the venv bin directory first in PATH, 'python' now refers to the venv python
ENV PATH="/app/.venv/bin:$PATH"

# 6. Copy service code
COPY services/notify-fan-out/ .

# Run as polling daemon
CMD ["uv", "run", "python", "main.py"]
