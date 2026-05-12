#!/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
ANNOTATIONS_DIR="$SCRIPT_DIR/../annotations";
ANNOTATIONS_BIN="$ANNOTATIONS_DIR/node_modules/.bin"
ENV_FILE="$SCRIPT_DIR/../app/config/.env";
source "$SCRIPT_DIR"/utils.sh;

check_file_exists "$ENV_FILE"
cd "$ANNOTATIONS_DIR";
npm i --include=dev;  # in dev mode, devDependencies includes aiiinotate. in prod, aiiinotate is in its own Docker container.
services_start;

"$ANNOTATIONS_BIN"/dotenvx run -f "$ENV_FILE" \
    -- "$ANNOTATIONS_BIN"/aiiinotate migrate apply;
