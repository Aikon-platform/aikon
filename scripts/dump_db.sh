#!/bin/bash

# HOW TO USE
# in the script directory
# sh dump_db.sh

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

. "$APP_ROOT"/app/config/.env

PGPASS_FILE="./.pgpass"
echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USERNAME:$DB_PASSWORD" > "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"
export PGPASSFILE='./.pgpass'

pg_dump -h "$DB_HOST" -U "$DB_USERNAME" -d "$DB_NAME" > "$(date +%Y-%m-%d)_dump_$DB_NAME".sql
