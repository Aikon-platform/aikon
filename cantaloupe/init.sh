#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cp $SCRIPT_DIR/cantaloupe.properties{.template,}
CONFIG_CANTALOUPE=$SCRIPT_DIR/cantaloupe.properties

sudo chmod +x $SCRIPT_DIR/start.sh

source $SCRIPT_DIR/.env
sed -i "s|BASE_URI|$BASE_URI|g" "$CONFIG_CANTALOUPE"
sed -i "s|FILE_SYSTEM_SOURCE|$FILE_SYSTEM_SOURCE|g" "$CONFIG_CANTALOUPE"
sed -i "s/HTTP_PORT/$HTTP_PORT/g" "$CONFIG_CANTALOUPE"
sed -i "s/HTTPS_PORT/$HTTPS_PORT/g" "$CONFIG_CANTALOUPE"
sed -i "s|LOG_PATH|$LOG_PATH|g" "$CONFIG_CANTALOUPE"
