#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")

source "$SCRIPT_DIR"/functions.sh

echoTitle "CANTALOUPE ENV GENERATION"
CANTALOUPE_ENV_FILE="$FRONT_DIR"/cantaloupe/.env
cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"
update_cantaloupe_env
bash "$FRONT_DIR"/cantaloupe/init.sh
