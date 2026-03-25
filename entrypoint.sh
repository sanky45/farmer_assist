#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! python manage.py dbshell --command="SELECT 1;" > /dev/null 2>&1; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Execute the main command
exec "$@"