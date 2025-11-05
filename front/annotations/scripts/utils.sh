#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
ROOT_DIR="$SCRIPT_DIR/..";
ENV_FILE="$ROOT_DIR/.env";

start_mongod() {
    if ! systemctl is-active --quiet mongod;
    then sudo systemctl start mongod;
    fi;
}

check_envfile() {
    if [ ! -f "$ENV_FILE" ];
    then echo "'.env' file does not exist. exiting... (at '$ENV_FILE')"; exit 1;
    fi;
}
