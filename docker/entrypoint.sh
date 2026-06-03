#!/bin/sh
set -e

# Ensure model cache and data dir are writable by the app user
chown -R app:app /app/models /app/data 2>/dev/null || true

exec "$@"
