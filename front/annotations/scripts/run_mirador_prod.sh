#!/bin/env bash

ENV_FILE=$1

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MIRADOR_DIR=$(dirname "$SCRIPT_DIR")
NPM_BIN="$MIRADOR_DIR"/node_modules/.bin

if [ ! -f "$ENV_FILE" ]; then
    echo "MIRADOR: Could not fetch .env file. Exiting..."
    exit 1;
fi;
if [ ! -d "$NPM_BIN" ]; then
    echo "MIRADOR: Could not find node_modules/.bin directory. Exiting..."
    exit 1;
fi;

source "$ENV_FILE"
if [ -z "$MIRADOR_PORT" ]; then
    echo "MIRADOR: Variable MIRADOR_PORT is unset in ENV_FILE. Exiting..."
    exit 1;
fi;

rm -rf "$MIRADOR_DIR"/dist "$MIRADOR_DIR"/.parcel-cache
"$NPM_BIN"/dotenvx run -f "$ENV_FILE" -- \
"$NPM_BIN"/parcel "$MIRADOR_DIR"/src/index.html \
    --port "$MIRADOR_PORT" \
    --dist-dir "$MIRADOR_DIR/dist";
