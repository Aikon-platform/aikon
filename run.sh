#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$SCRIPT_DIR/front"
API_DIR="$SCRIPT_DIR/api"

source "$FRONT_DIR/scripts/utils.sh"

declare -a ALL_PIDS=()

cleanup() {
    cleanup_pids "${ALL_PIDS[*]}" "celery|dramatiq|flask|runserver|cantaloupe|jetty" "$PASSWORD"
    exit 0
}

trap cleanup INT TERM HUP

read -s -p "Enter your sudo password: " PASSWORD
echo

color_echo blue "STARTING FRONT..."
(cd "$FRONT_DIR" && START_MODE="CHILD" bash run.sh "$PASSWORD") &
ALL_PIDS+=($!)

sleep 2

color_echo blue "STARTING API..."
(cd "$API_DIR" && START_MODE="CHILD" bash run.sh) &
ALL_PIDS+=($!)

sleep 2

color_echo magenta "All services started. Press Ctrl+C to stop everything."
wait
