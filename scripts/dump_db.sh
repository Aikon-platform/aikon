#!/bin/bash

# HOW TO USE
# in the script directory
# bash dump_db.sh

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

. "$APP_ROOT"/app/config/.env

PGPASS_FILE="./.pgpass"
echo "$DB_HOST:$DB_PORT:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"
export PGPASSFILE='./.pgpass'

pg_dump -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$(date +%Y-%m-%d)_dump_$POSTGRES_DB".sql
