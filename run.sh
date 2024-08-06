#! /bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BIN="$ROOT_DIR"/.env/bin
SCHEDULE_FILE="$ROOT_DIR/celery/celerybeat-schedule"

read -s -p "Enter your sudo password: " password
echo

(trap 'kill 0' SIGINT;
    ("$BIN"/celery -A app.config.celery worker -B -c 1 --loglevel=DEBUG -P threads) &
    ("$BIN"/celery -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=DEBUG) &
    ("$BIN"/python app/manage.py runserver localhost:8000)
)
