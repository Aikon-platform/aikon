#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_DIR="$FRONT_DIR"/app

source "$SCRIPT_DIR"/utils.sh

echo_title "VIRTUAL ENVIRONMENT SET UP"

uv sync --group=dev --directory="$APP_DIR";
