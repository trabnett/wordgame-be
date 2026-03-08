#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; socket.create_connection(('db', 5432))" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

python manage.py migrate --noinput

exec "$@"
