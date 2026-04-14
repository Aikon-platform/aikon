#!/bin/env bash

ENV_FILE="$1"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MIRADOR_DIR=$(dirname "$SCRIPT_DIR")  # parent of SCRIPT_DIR = Mirador docker workdir
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

# PUBLIC_URL is the path at which parcel serves the files.
# in locahost, they are served at http://localhost:$MIRADOR_PORT
# in docker, they are sered at http://localhost/mirador, corresponding to our NGINX config.
if [ "$DOCKER" = "True" ]; then
    PUBLIC_URL="/mirador/"
else
    PUBLIC_URL="/"
fi;

rm -rf "$MIRADOR_DIR"/dist "$MIRADOR_DIR"/.parcel-cache
"$NPM_BIN"/dotenvx run -f "$ENV_FILE" -- \
"$NPM_BIN"/parcel "$MIRADOR_DIR"/src/index.html \
    --port "$MIRADOR_PORT" \
    --public-url  "$PUBLIC_URL" \
    --dist-dir "$MIRADOR_DIR/dist";
