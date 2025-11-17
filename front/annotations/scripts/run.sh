#!/usr/bin/env bash

source "$SCRIPT_DIR/utils.sh"

cd "$ROOT_DIR"

check_envfile;

aiiinotate --env "$ENV_FILE" -- serve prod &

rm -rf dist .parcel-cache && parcel src/index.html;

# once the above command returns, kill aiiinotate (MainThread = nodejs parent thread).
kill $(pgrep MainThread);
