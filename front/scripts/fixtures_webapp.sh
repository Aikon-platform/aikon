#!/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
FRONT_DIR=$(readlink --canonicalize "$SCRIPT_DIR/..")
APP_DIR="$FRONT_DIR/app"
WEBAPP_DIR="$APP_DIR/webapp"
FIXTURES_DIR="$WEBAPP_DIR/fixtures"
MANAGE="$APP_DIR/manage.py"

source "$FRONT_DIR/venv/bin/activate" || exit 1

exists() {
    [ -d "$1" ] || [ -f "$1" ] && echo "y" || echo "n"
}

dump_fixture() {
    model="$1"
    python "$MANAGE" dumpdata "webapp.$model" --indent=2 > "$FIXTURES_DIR/$model.json"
}

dump_fixture "Regions"
dump_fixture "Digitization"
dump_fixture "Witness"
