#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

db_name=$(get_env_value "POSTGRES_DB" "$APP_ENV")
db_user=$(get_env_value "POSTGRES_USER" "$APP_ENV")
db_psw=$(get_env_value "POSTGRES_PASSWORD" "$APP_ENV")

echo_title "DATABASE GENERATION"

color_echo yellow "\n⚠️ The script will create a new database named $db_name and an app user named $db_user with password $db_psw (all defined in aikon_dir/front/config/.env)"
options=("ok")
printf "%s\n" "${options[@]}" | fzy
bash "$SCRIPT_DIR"/new_db.sh "$db_name"

# TOOD move new_db here ?
