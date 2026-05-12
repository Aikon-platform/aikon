#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"  # front/
# VENV_PATH="$APP_ROOT"/app/.venv
VENV_PATH=/home/aikon/.venv
CELERY_BIN="$VENV_PATH"/bin/celery  # NOTE: `uv run celery` does not work so we fetch the binary directly from the venv.
SCHEDULE_FILE="$APP_ROOT/celery/celerybeat-schedule"

export PYTHONPATH=$APP_ROOT
export DJANGO_SETTINGS_MODULE="app.config.settings"

cd "$APP_ROOT" || exit 1
"$CELERY_BIN" -A app.config.celery worker --loglevel=info -P threads
"$CELERY_BIN" -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=info
