#!/bin/env bash

# TODO check setup for svelte

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")

source "$SCRIPT_DIR"/utils.sh

if ! command -v npm &> /dev/null; then
    echo_title "INSTALL NVM & NODE"
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    nvm install node
    npm install -g webpack webpack-cli
fi

echo_title "SVELTE SETUP"
cd "$FRONT_DIR"/app/webpack || echo "Webpack directory not found: $FRONT_DIR/app/webpack"
npm init
color_echo blue "\nCompile svelte components using: "
color_echo cyan "              npm run build"
