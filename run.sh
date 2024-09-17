#! /bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BIN="$ROOT_DIR"/venv/bin
SCHEDULE_FILE="$ROOT_DIR/celery/celerybeat-schedule"

read -s -p "Enter your sudo password: " password
echo

(trap 'kill 0' SIGINT;
    ("$BIN"/celery -A app.config.celery worker -B -c 1 --loglevel=DEBUG -P threads) &
    ("$BIN"/celery -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=DEBUG) &
    ("$BIN"/python app/manage.py runserver localhost:1234) &
    (echo "$password" | sudo -S java -Dcantaloupe.config="$ROOT_DIR"/cantaloupe/cantaloupe.properties -Xmx2g -jar "$ROOT_DIR"/cantaloupe/cantaloupe-4.1.11.war > /dev/null 2>&1) &
    (cd "$ROOT_DIR"/sas/ && mvn jetty:run -q);
)
