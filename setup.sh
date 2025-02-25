#!/bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
AIKON_DIR="$ROOT_DIR/front"
API_DIR="$ROOT_DIR/api"
AIKON_SCRIPT_DIR="$AIKON_DIR/scripts"

AIKON_SETUP="$AIKON_DIR/scripts/setup.sh"
API_SETUP="$API_DIR/setup.sh"

source "$AIKON_SCRIPT_DIR/functions.sh"

git submodule init
git submodule update

# TODO create accelerate setup script to define only important env variables

echoTitle "AIKON BUNDLE INSTALL"

colorEcho green "AIKON installation..."
cd "$AIKON_DIR";

if ! bash "$AIKON_SETUP"; then
    colorEcho red "AIKON setup encountered an error"
    exit 1
fi

colorEcho green "API installation..."
cd "$API_DIR"

if ! bash "$API_SETUP"; then
    colorEcho red "API setup encountered an error"
    exit 1
fi

# replace CV_API_URL in aikon/.env by localhost:discover-api/.env.dev => $API_DEV_PORT
api_port=$(grep "API_DEV_PORT" "$API_DIR/.env.dev" | cut -d'=' -f2)
api_url=localhost:$(echo "$api_port" | tr -d '"')
sed -i "" -e "s~^CV_API_URL=.*~CV_API_URL=$api_url~" "$AIKON_DIR/app/config/.env"

echoTitle "🎉 AIKON & DISCOVER ARE SET UP! 🎉"
colorEcho blue "\nYou can now run the app and API with: "
colorEcho green "              bash run.sh"

user=$(grep "POSTGRES_USER" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
password=$(grep "POSTGRES_PASSWORD" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
colorEcho blue '\nConnect to app using:'
echo -e "          👤 $user"
echo -e "          🔑 $password"
