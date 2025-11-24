#!/bin/bash

SUDO_PSW="$1"
FRONT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ENV_FILE="$FRONT_DIR/app/config/.env"
BIN="$FRONT_DIR"/venv/bin
SCHEDULE_FILE="$FRONT_DIR/celery/celerybeat-schedule"
ANNOTATIONS_DIR="$FRONT_DIR/annotations"
ANNOTATIONS_BIN="$FRONT_DIR/annotations/node_modules/.bin"
FRONT_PORT=${FRONT_PORT:-8000}

declare -a PIDS=()

source "$ENV_FILE"
source "$FRONT_DIR/scripts/utils.sh"

get_password && echo || exit

# Cleanup function if running standalone
if [ "$START_MODE" != "CHILD" ]; then
    cleanup() {
        cleanup_pids "${PIDS[*]}" "celery|runserver|cantaloupe|jetty|multiprocessing" "$SUDO_PSW"
        exit 0
    }

    trap cleanup INT TERM HUP
fi

# start all services just to be sure
services_start

"$BIN"/celery -A app.config.celery worker -B -c 1 --loglevel=INFO -P threads &
CELERY_WORKER_PID=$!
PIDS+=($CELERY_WORKER_PID)

"$BIN"/celery -A app.config.celery beat --schedule="$SCHEDULE_FILE" --loglevel=INFO &
CELERY_BEAT_PID=$!
PIDS+=($CELERY_BEAT_PID)

"$BIN"/python app/manage.py runserver localhost:"$FRONT_PORT" &
DJANGO_PID=$!
PIDS+=($DJANGO_PID)

echo "$SUDO_PSW" | sudo -S java -Dcantaloupe.config="$FRONT_DIR"/cantaloupe/cantaloupe.properties -Xmx2g -jar "$FRONT_DIR"/cantaloupe/cantaloupe-4.1.11.war > /dev/null 2>&1 &
CANTALOUPE_PID=$!
PIDS+=($CANTALOUPE_PID)

"$ANNOTATIONS_BIN"/aiiinotate --env "$ENV_FILE" -- serve prod &
AIIINOTATE_PID=$!
PIDS+=($AIIINOTATE_PID)

rm -rf "$ANNOTATIONS_DIR"/dist "$ANNOTATIONS_DIR"/.parcel-cache
"$ANNOTATIONS_BIN"/parcel "$ANNOTATIONS_DIR"/src/index.html --port "$MIRADOR_PORT" &
MIRADOR_PID=$!
PIDS+=($MIRADOR_PID)

color_echo cyan "Celery worker PID  $CELERY_WORKER_PID"
color_echo cyan "C2elery beat PID    $CELERY_BEAT_PID"
color_echo cyan "Django PID         $DJANGO_PID"
color_echo cyan "Cantaloupe PID     $CANTALOUPE_PID"
color_echo cyan "AIIINOTATE PID     $AIIINOTATE_PID"
color_echo cyan "MIRADOR PID        $MIRADOR_PID"

if [ "$START_MODE" != "CHILD" ]; then
    color_echo magenta "Press Ctrl+C to stop all frontend processes"
    wait
else
    (tail -f /dev/null >/dev/null 2>&1) &
    TAIL_PID=$!
    PIDS+=($TAIL_PID)
    wait $TAIL_PID
fi
