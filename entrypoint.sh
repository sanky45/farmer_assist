#!/bin/sh
set -e

# Apply database migrations
python manage.py migrate --noinput

# Collect static files (if needed)
python manage.py collectstatic --noinput

# Run the main process
exec "$@"
