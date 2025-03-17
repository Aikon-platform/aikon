#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
CANTALOUPE_DIR="$FRONT_DIR"/cantaloupe

source "$SCRIPT_DIR"/utils.sh

echo_title "CANTALOUPE ENV GENERATION"

setup_cantaloupe "$INSTALL_MODE"
