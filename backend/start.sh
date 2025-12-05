#!/bin/bash

# Default to port 8000 if PORT is not set
PORT="${PORT:-8000}"

if [ "$RAILWAY_ENVIRONMENT_NAME" == "production" ] || [ "$ENVIRONMENT" == "production" ]; then
    echo "Running in Production Mode"
    # Use 'fastapi run' which is optimized for production
    # no watcher.py in production
    exec fastapi run app/main.py --host 0.0.0.0 --port "$PORT"
elif [ -f /.dockerenv ]; then
    echo "Running in Docker (Dev/Preview)"
    fastapi dev app/main.py --host 0.0.0.0 --port "$PORT" --reload &
    python watcher.py
    wait
else
    echo "Running locally with uv"
    uv run fastapi dev app/main.py --host 0.0.0.0 --port "$PORT" --reload &
    uv run python watcher.py
    wait
fi
