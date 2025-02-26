#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")

source "$SCRIPT_DIR"/functions.sh

INSTALL_TYPE=$(get_install_type "$1")

echoTitle "CANTALOUPE ENV GENERATION"

CANTALOUPE_ENV_FILE="$FRONT_DIR"/cantaloupe/.env
cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"

update_cantaloupe_env "$INSTALL_TYPE"
bash "$FRONT_DIR"/cantaloupe/init.sh
