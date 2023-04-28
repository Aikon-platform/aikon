#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cp $SCRIPT_DIR/cantaloupe.properties{.template,}

sudo chmod +x $SCRIPT_DIR/start.sh

source $SCRIPT_DIR/.env
sed -i "s|BASE_URI|$BASE_URI|g" $SCRIPT_DIR/cantaloupe.properties
sed -i "s|FILE_SYSTEM_SOURCE|$FILE_SYSTEM_SOURCE|g" $SCRIPT_DIR/cantaloupe.properties
sed -i "s/HTTP_PORT/$HTTP_PORT/g" $SCRIPT_DIR/cantaloupe.properties
sed -i "s/HTTPS_PORT/$HTTPS_PORT/g" $SCRIPT_DIR/cantaloupe.properties
sed -i "s|LOG_PATH|$LOG_PATH|g" $SCRIPT_DIR/cantaloupe.properties
