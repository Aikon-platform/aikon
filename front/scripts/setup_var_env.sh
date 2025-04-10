#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/utils.sh;

echo_title "APP ENV GENERATION"

update_app_env "$APP_ENV" "$FRONT_DIR" "$INSTALL_MODE"
