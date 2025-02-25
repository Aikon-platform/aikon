#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_DIR="$FRONT_DIR"/app

source "$SCRIPT_DIR"/functions.sh

echoTitle "VIRTUAL ENVIRONMENT SET UP"

cd "$FRONT_DIR"
python3.10 -m venv venv
source venv/bin/activate

# solve dependency conflicts and install errors
pip install --upgrade pip
pip install --upgrade wheel
pip install "setuptools==70.0.0"

pip install -r "$APP_DIR"/requirements-dev.txt
pre-commit install
