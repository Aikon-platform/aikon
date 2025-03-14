#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
CANTALOUPE_DIR="$FRONT_DIR"/cantaloupe

source "$SCRIPT_DIR"/functions.sh

echo_title "CANTALOUPE ENV GENERATION"

CANTALOUPE_ENV_FILE="$FRONT_DIR"/cantaloupe/.env
cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"

update_cantaloupe_env "$INSTALL_MODE"
update_cantaloupe_properties "$CANTALOUPE_DIR"
# bash "$FRONT_DIR"/cantaloupe/init.sh
