#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

VENV_PATH="$APP_ROOT/venv"
export PYTHONPATH=$APP_ROOT
source "$VENV_PATH/bin/activate"

. "$APP_ROOT"/app/config/.env

cd "$APP_ROOT" || exit 1
"$VENV_PATH"/bin/gunicorn --access-logfile "$SCRIPT_DIR"/stdout.log \
                          --error-logfile "$SCRIPT_DIR"/error.log  \
                          --workers 3 \
                          --bind unix:/run/"$APP_NAME-gunicorn".sock \
                          --timeout 150 \
                          app.config.wsgi:application
