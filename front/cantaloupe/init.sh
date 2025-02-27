#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cp "$SCRIPT_DIR"/cantaloupe.properties{.template,}
CONFIG_CANTALOUPE="$SCRIPT_DIR"/cantaloupe.properties

chmod +x "$SCRIPT_DIR"/start.sh

source "$SCRIPT_DIR"/.env
source "$SCRIPT_DIR"/../scripts/functions.sh

sed_repl_inplace "s~BASE_URI~$BASE_URI~" "$CONFIG_CANTALOUPE"
sed_repl_inplace "s~FILE_SYSTEM_SOURCE~$FILE_SYSTEM_SOURCE~" "$CONFIG_CANTALOUPE"
sed_repl_inplace "s~HTTP_PORT~$HTTP_PORT~" "$CONFIG_CANTALOUPE"
sed_repl_inplace "s~HTTPS_PORT~$HTTPS_PORT~" "$CONFIG_CANTALOUPE"
sed_repl_inplace "s~LOG_PATH~$LOG_PATH~" "$CONFIG_CANTALOUPE"
