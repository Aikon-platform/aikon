#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# bash alter_db.sh

get_os() {
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     os=Linux;;
        Darwin*)    os=Mac;;
        CYGWIN*)    os=Cygwin;;
        MINGW*)     os=MinGw;;
        MSYS_NT*)   os=Git;;
        *)          os="UNKNOWN:${unameOut}"
    esac
    echo "${os}"
}

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

PGPASS_FILE="./.pgpass"
echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USERNAME:$DB_PASSWORD" > "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"
export PGPASSFILE='./.pgpass'

case $(get_os) in
    Linux)
        command="sudo -i -u $DB_USERNAME psql -d $DB_NAME"
        ;;
    Mac)
        command="psql -U $DB_USERNAME -d $DB_NAME"
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
