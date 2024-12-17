FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    DJANGO_SETTINGS_MODULE=config.settings.production
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install required system packages
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project --no-editable --no-dev

# Copy the project
COPY . .

# Install the project
RUN uv sync --frozen --no-editable --no-dev

# Create and switch to non-root user
RUN adduser --disabled-password --gecos '' django_user && \
    chown -R django_user:django_user /app
USER django_user

# Expose the port
EXPOSE 8000

# Run migrations and start the server
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
