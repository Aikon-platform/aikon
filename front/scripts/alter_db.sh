#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# bash alter_db.sh

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/functions.sh

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

PGPASS_FILE="./.pgpass"
echo "$DB_HOST:$DB_PORT:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"
export PGPASSFILE='./.pgpass'

case $(get_os) in
    Linux)
        command="sudo -i -u $POSTGRES_USER psql -d $POSTGRES_DB"
        ;;
    Mac)
        command="psql -U $POSTGRES_USER -d $POSTGRES_DB"
        ;;
    *)
        echo "Unsupported OS: you need to create the database manually"
        exit 1
        ;;
esac

# list all databases with
#$command -c '\l'

# put your commands here
#$command -c "\dt"
$command -c "SELECT COUNT(*) FROM public.webapp_regionpair;"
$command -c "DELETE FROM public.webapp_regionpair WHERE score < 25;"
$command -c "SELECT COUNT(*) FROM public.webapp_regionpair;"
