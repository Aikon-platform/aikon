#!/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CONFIG="$SCRIPT_DIR/cantaloupe.properties"
TEMPLATE="$SCRIPT_DIR/cantaloupe.properties.template"

[[ -f "$TEMPLATE" ]] || { echo "missing $TEMPLATE"; exit 1; }

sed -e "s~CANTALOUPE_BASE_URI~$CANTALOUPE_BASE_URI~g" \
    -e "s~CANTALOUPE_IMG~$CANTALOUPE_IMG~g" \
    -e "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~g" \
    -e "s~CANTALOUPE_PORT_HTTPS~$CANTALOUPE_PORT_HTTPS~g" \
    "$SCRIPT_DIR/cantaloupe.properties.template" > "$CONFIG"

exec java -Dcantaloupe.config="$CONFIG" -Xmx2g -jar "$SCRIPT_DIR/cantaloupe-4.1.11.war"
