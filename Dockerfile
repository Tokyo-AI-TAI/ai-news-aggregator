FROM python:3.12-slim

ARG DJANGO_SETTINGS_MODULE=config.settings.production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

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

# Install playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji \
    libxtst6

RUN uv run playwright install --with-deps

RUN chmod +x ./entrypoint.sh

# Install cron
RUN apt-get update && apt-get install -y cron

# Add crontab file
COPY crontab /etc/cron.d/app-cron
RUN chmod 0644 /etc/cron.d/app-cron
RUN crontab /etc/cron.d/app-cron

# Set the entrypoint
CMD ["./entrypoint.sh"]
