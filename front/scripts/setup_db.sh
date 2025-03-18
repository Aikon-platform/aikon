#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/utils.sh

db_name=$(get_env_value "POSTGRES_DB" "$APP_ENV")
db_user=$(get_env_value "POSTGRES_USER" "$APP_ENV")
db_psw=$(get_env_value "POSTGRES_PASSWORD" "$APP_ENV")

echo_title "DATABASE GENERATION"

db=$(color_echo 'red' "$db_name")
user="$(color_echo 'yellow' ', the django admin user') $(color_echo 'red' "$db_user")"
psw="$(color_echo 'yellow' ' with password') $(color_echo 'red' "$db_psw")"

color_echo yellow "\n⚠️ The script will create a new database using information provided in aikon_dir/front/config/.env"
color_echo yellow "The database will be named $db$user$psw"
color_echo yellow "You will be prompted for your postgres password. If you enter the wrong password, the database initialization step will fail."

options=("ok")
printf "%s\n" "${options[@]}" | fzy
bash "$SCRIPT_DIR"/new_db.sh "$db_name"

# TODO move new_db here ?
