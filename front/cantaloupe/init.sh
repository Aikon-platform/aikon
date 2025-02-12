#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cp "$SCRIPT_DIR"/cantaloupe.properties{.template,}
CONFIG_CANTALOUPE="$SCRIPT_DIR"/cantaloupe.properties

chmod +x "$SCRIPT_DIR"/start.sh

source "$SCRIPT_DIR"/.env

sed -i "" -e "s~BASE_URI~$BASE_URI~" "$CONFIG_CANTALOUPE"
sed -i "" -e "s~FILE_SYSTEM_SOURCE~$FILE_SYSTEM_SOURCE~" "$CONFIG_CANTALOUPE"
sed -i "" -e "s~HTTP_PORT~$HTTP_PORT~" "$CONFIG_CANTALOUPE"
sed -i "" -e "s~HTTPS_PORT~$HTTPS_PORT~" "$CONFIG_CANTALOUPE"
sed -i "" -e "s~LOG_PATH~$LOG_PATH~" "$CONFIG_CANTALOUPE"
