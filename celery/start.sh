#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

VENV_PATH="$APP_ROOT/venv"
source "$VENV_PATH/bin/activate"

"$VENV_PATH"/bin/celery -A app.config.celery worker --loglevel=info -P threads
