#!/bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
AIKON_DIR="$ROOT_DIR/front"
API_DIR="$ROOT_DIR/api"

AIKON_SETUP="$AIKON_DIR/scripts/setup.sh"
API_SETUP="$API_DIR/setup.sh"

git submodule init
git submodule update

# TODO create accelerate setup script to define only important env variables

echo_title "AIKON BUNDLE INSTALL"

color_echo green "AIKON installation..."
cd "$AIKON_DIR";

if ! bash "$AIKON_SETUP"; then
    color_echo red "AIKON setup encountered an error"
    exit 1
fi

color_echo green "API installation..."
cd "$API_DIR"

if ! bash "$API_SETUP"; then
    color_echo red "API setup encountered an error"
    exit 1
fi

# replace CV_API_URL in aikon/.env by localhost:discover-api/.env.dev => $API_DEV_PORT
api_port=$(grep "API_DEV_PORT" "$API_DIR/.env.dev" | cut -d'=' -f2)
api_url=localhost:$(echo "$api_port" | tr -d '"')
sed -i "" -e "s~^CV_API_URL=.*~CV_API_URL=$api_url~" "$AIKON_DIR/app/config/.env"

echo_title "🎉 AIKON & DISCOVER ARE SET UP! 🎉"
color_echo blue "\nYou can now run the app and API with: "
color_echo green "              bash run.sh"

user=$(grep "POSTGRES_USER" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
password=$(grep "POSTGRES_PASSWORD" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
color_echo blue '\nConnect to app using:'
echo -e "          👤 $user"
echo -e "          🔑 $password"
