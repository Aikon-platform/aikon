#!/bin/bash

PASSWORD="$1"
FRONT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BIN="$FRONT_DIR"/venv/bin
SCHEDULE_FILE="$FRONT_DIR/celery/celerybeat-schedule"
FRONT_PORT=${FRONT_PORT:-8000}

declare -a PIDS=()

source "$FRONT_DIR/app/config/.env"
source "$FRONT_DIR/scripts/utils.sh"

if [ -z "$PASSWORD" ]; then
    read -s -p "Enter your sudo password: " PASSWORD
    echo
fi

# Cleanup function if running standalone
if [ "$START_MODE" != "CHILD" ]; then
    cleanup() {
        cleanup_pids "${PIDS[*]}" "celery|runserver|cantaloupe|jetty" "$PASSWORD"
        exit 0
    }

    trap cleanup INT TERM HUP
fi

"$BIN"/celery -A app.config.celery worker -B -c 1 --loglevel=INFO -P threads &
CELERY_WORKER_PID=$!
PIDS+=($CELERY_WORKER_PID)

"$BIN"/celery -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=INFO &
CELERY_BEAT_PID=$!
PIDS+=($CELERY_BEAT_PID)

"$BIN"/python app/manage.py runserver localhost:"$FRONT_PORT" &
DJANGO_PID=$!
PIDS+=($DJANGO_PID)

echo "$PASSWORD" | sudo -S java -Dcantaloupe.config="$FRONT_DIR"/cantaloupe/cantaloupe.properties -Xmx2g -jar "$FRONT_DIR"/cantaloupe/cantaloupe-4.1.11.war > /dev/null 2>&1 &
CANTALOUPE_PID=$!
PIDS+=($CANTALOUPE_PID)

(cd "$FRONT_DIR"/sas/ && mvn jetty:run -q) &
SAS_PID=$!
PIDS+=($SAS_PID)

color_echo cyan "Celery worker PID  $CELERY_WORKER_PID"
color_echo cyan "Celery beat PID    $CELERY_BEAT_PID"
color_echo cyan "Django PID         $DJANGO_PID"
color_echo cyan "Cantaloupe PID     $CANTALOUPE_PID"
color_echo cyan "SAS PID            $SAS_PID"

if [ "$START_MODE" != "CHILD" ]; then
    color_echo magenta "Press Ctrl+C to stop all frontend processes"
    wait
else
    (tail -f /dev/null >/dev/null 2>&1) &
    TAIL_PID=$!
    PIDS+=($TAIL_PID)
    wait $TAIL_PID
fi
