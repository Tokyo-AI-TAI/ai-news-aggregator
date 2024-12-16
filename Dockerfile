# Use Python 3.12 slim as base
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable --no-dev

# Copy the project into the intermediate image
COPY . /app

# Sync the project (since dependencies are already installed, this will only install the project code)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

# Create non-root user
RUN adduser --disabled-password --gecos '' django_user

FROM python:3.12-slim

# Set environment variables again for the final image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the environment, but not the source code
COPY --from=builder --chown=django_user:django_user /app/.venv /app/.venv

# Switch to non-root user
USER django_user

# Run the application
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
