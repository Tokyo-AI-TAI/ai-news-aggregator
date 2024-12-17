FROM python:3.12-slim

ARG DJANGO_SECRET_KEY
ARG DJANGO_ADMIN_URL
ARG DJANGO_ALLOWED_HOSTS

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY} \
    DJANGO_ADMIN_URL=${DJANGO_ADMIN_URL} \
    DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}

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

# Collect static files
RUN uv run python manage.py collectstatic --noinput

# Create and switch to non-root user
RUN adduser --disabled-password --gecos '' django_user && \
    chown -R django_user:django_user /app
USER django_user

# Expose the port
EXPOSE 8000

# Run migrations and start the server
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
