#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_DIR="$FRONT_DIR"/app

source "$SCRIPT_DIR"/functions.sh

echoTitle "VIRTUAL ENVIRONMENT SET UP"

cd "$FRONT_DIR"
python3.10 -m venv venv
source venv/bin/activate
pip install -r "$APP_DIR"/requirements-dev.txt
pre-commit install
