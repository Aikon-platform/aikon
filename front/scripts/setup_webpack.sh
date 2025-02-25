#!/bin/env bash

# TODO check setup for svelte

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")

source "$SCRIPT_DIR"/functions.sh

if ! command -v npm &> /dev/null; then
    echoTitle "INSTALL NVM & NODE"
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    nvm install node
    npm install -g webpack webpack-cli
fi

echoTitle "SVELTE SETUP"
cd "$FRONT_DIR"/app/webpack || echo "Webpack directory not found: $FRONT_DIR/app/webpack" && exit
npm init
colorEcho blue "\nCompile svelte components using: "
colorEcho cyan "              npm run build"
