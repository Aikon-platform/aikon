#! /bin/bash

FRONT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BIN="$FRONT_DIR"/venv/bin
SCHEDULE_FILE="$FRONT_DIR/celery/celerybeat-schedule"

source "$FRONT_DIR/app/config/.env"
FRONT_PORT=${FRONT_PORT:-8000}

read -s -p "Enter your sudo password: " password
echo

(trap 'kill 0' SIGINT;
    ("$BIN"/celery -A app.config.celery worker -B -c 1 --loglevel=DEBUG -P threads) &
    ("$BIN"/celery -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=DEBUG) &
    ("$BIN"/python app/manage.py runserver localhost:"$FRONT_PORT") &
    (echo "$password" | sudo -S java -Dcantaloupe.config="$FRONT_DIR"/cantaloupe/cantaloupe.properties -Xmx2g -jar "$FRONT_DIR"/cantaloupe/cantaloupe-4.1.11.war > /dev/null 2>&1) &
    (cd "$FRONT_DIR"/sas/ && mvn jetty:run -q);
)
