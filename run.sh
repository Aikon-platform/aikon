#!/bin/bash

FRONT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/front" >/dev/null 2>&1 && pwd )"
API_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/api" >/dev/null 2>&1 && pwd )"

FRONT_RUN="$FRONT_DIR/run.sh"
API_RUN="$API_DIR/run.sh"

front_pid=""
api_pid=""

read -s -p "Enter your sudo password: " PASSWORD

cleanup() {
    echo "Shutting down all processes..."
    [ -n "$front_pid" ] && kill "$front_pid"
    [ -n "$api_pid" ] && kill "$api_pid"
    wait
    echo "All processes terminated."
    exit 0
}

trap cleanup SIGINT SIGTERM

(cd "$FRONT_DIR" && bash "$FRONT_RUN" "$PASSWORD") &
front_pid=$!

(cd "$API_DIR" && bash "$API_RUN") &
api_pid=$!

wait
