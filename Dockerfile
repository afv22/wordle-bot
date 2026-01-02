FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY main.py ./
COPY src/ ./src/
COPY wordlists/ ./wordlists/ ./

# Run the bot
CMD ["uv", "run", "python", "main.py"]
