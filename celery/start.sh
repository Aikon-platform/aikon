#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

VENV_PATH="$APP_ROOT/venv"
export PYTHONPATH=$APP_ROOT
export DJANGO_SETTINGS_MODULE="app.config.settings"
source "$VENV_PATH/bin/activate"

cd "$APP_ROOT" || exit 1
"$VENV_PATH"/bin/celery -A app.config.celery worker --loglevel=info -P threads
