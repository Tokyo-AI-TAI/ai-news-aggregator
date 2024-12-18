#!/usr/bin/env sh
set -e

# Run migrations
uv run python manage.py migrate --noinput

# Start Gunicorn
exec uv run gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level debug \
    --error-logfile - \
    --access-logfile -
