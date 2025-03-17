#!/bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$ROOT_DIR/front"
API_DIR="$ROOT_DIR/api"
FRONT_ENV="$FRONT_DIR/app/config/.env"

FRONT_SETUP="$FRONT_DIR/scripts/setup.sh"
API_SETUP="$API_DIR/setup.sh"
source "$FRONT_DIR"/scripts/utils.sh

color_echo blue "\nInstalling prompt utility fzy..."
if [ "$OS" = "Linux" ]; then
    sudo apt install fzy
elif [ "$OS" = "Mac" ]; then
    brew install fzy
else
    color_echo red "\nUnsupported OS: $OS"
    exit 1
fi

color_echo blue "Do you want to init the api/ submodule (WARNING: this will checkout from your current API branch to a detached head, resetting all changes made to the API) ?"
options=("yes" "no")
answer=$(printf "%s\n" "${options[@]}" | fzy)
if [ "$answer" = "yes" ]; then
    git submodule init
    git submodule update
fi

echo_title "AIKON BUNDLE INSTALL"

color_echo green "AIKON installation..."
cd "$FRONT_DIR";

if ! bash "$FRONT_SETUP"; then
    color_echo red "AIKON setup encountered an error"
    exit 1
fi

color_echo green "API installation..."
cd "$API_DIR"

if ! bash "$API_SETUP"; then
    color_echo red "API setup encountered an error"
    exit 1
fi

# replace API_URL in aikon/.env by localhost:api/.env.dev => $API_PORT
api_port=$(grep "API_PORT" "$API_DIR/.env.dev" | cut -d'=' -f2)
api_url=localhost:$(echo "$api_port" | tr -d '"')
sed_repl_inplace "s~^API_URL=.*~API_URL=$api_url~" "$FRONT_ENV"

echo_title "🎉 FRONT & API ARE SET UP! 🎉"
color_echo blue "\nYou can now run the app and API with: "
color_echo green "              bash run.sh"

source "$FRONT_ENV"
color_echo blue '\nConnect to app using:'
echo -e "          👤 $POSTGRES_USER"
echo -e "          🔑 $POSTGRES_PASSWORD"
