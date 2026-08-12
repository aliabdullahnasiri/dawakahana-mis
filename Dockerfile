FROM python:3.14.6

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies first for better Docker caching
COPY pyproject.toml uv.lock ./

# Copy application
COPY src ./src
COPY migrations ./migrations
COPY translations ./
COPY run.py ./
COPY README.md ./

RUN uv sync --frozen --no-dev

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--worker-class", "gevent", "--timeout", "120", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
