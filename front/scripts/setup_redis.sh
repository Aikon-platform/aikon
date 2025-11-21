#!/bin/env bash

# NOTE : delete this script ?

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR"/utils.sh

echo_title "REDIS DATABASE INITIALIZATION"
services_start
