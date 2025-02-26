#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh;

INSTALL_TYPE=$(get_install_type "$1")

echoTitle "APP ENV GENERATION"

cp "$APP_ENV".template "$APP_ENV"
update_dotenv "$APP_ENV" "$FRONT_DIR" "$INSTALL_TYPE"
