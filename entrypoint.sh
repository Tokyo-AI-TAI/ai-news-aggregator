#!/usr/bin/env sh
set -e

# Run migrations
uv run python manage.py migrate --noinput

# Collect static files
uv run python manage.py collectstatic --noinput

# Run compress
uv run python manage.py compress

# Run check
uv run python manage.py check --deploy

# Start Gunicorn
uv run gunicorn config.wsgi
