#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
ANNOTATIONS_DIR="$SCRIPT_DIR/../annotations";
ENV_FILE="$SCRIPT_DIR/../app/config/.env";
source "$SCRIPT_DIR"/utils.sh;

check_file_exists "$ENV_FILE"
cd "$ANNOTATIONS_DIR";
npm i;
start_mongod;

aiiinotate --env "$ENV_FILE" -- migrate apply;
