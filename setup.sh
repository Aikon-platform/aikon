#!/bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$ROOT_DIR/front"
API_DIR="$ROOT_DIR/api"
FRONT_ENV="$FRONT_DIR/app/config/.env"

FRONT_SETUP="$FRONT_DIR/scripts/setup.sh"
API_SETUP="$API_DIR/setup.sh"
source "$FRONT_DIR"/scripts/utils.sh

get_password && echo || exit

color_echo blue "\nInstalling prompt utility fzy..."
if [ "$OS" = "Linux" ]; then
    echo "$PASSWORD" | sudo -S apt install fzy
elif [ "$OS" = "Mac" ]; then
    brew install fzy
else
    color_echo red "\nUnsupported OS: $OS"
    exit 1
fi

INSTALL_MODE="full_install"
choose_install_mode() {
    color_echo blue "Do you want to run a full install or a quick install (skips defining basic env variables, perfect for dev)?"
    options=("quick install" "full install")
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    INSTALL_MODE="${answer/ /_}"  # "quick_install" or "full_install", will default to "full_install"
    export INSTALL_MODE="$INSTALL_MODE"
    echo ""
    color_echo cyan "Running a $answer! 🚀"
    echo ""
}
choose_install_mode

if [ ! -d "$API_DIR" ]; then
    git submodule init
    git submodule update
else
    color_echo blue "Do you want to init the api/ submodule (⚠️ this will checkout from your current API branch to a detached head, resetting all changes made to the API)?"
    options=("yes" "no")
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    if [ "$answer" = "yes" ]; then
        git submodule init
        git submodule update
    fi
fi

echo_title "AIKON BUNDLE INSTALL"

color_echo green "Front installation..."
cd "$FRONT_DIR";

if ! bash "$FRONT_SETUP"; then
    color_echo red "AIKON setup encountered an error"
    exit 1
fi

color_echo green "API installation..."
source "$FRONT_ENV"

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
color_echo green "          $ bash run.sh"

color_echo blue '\nConnect to app using:'
echo -e "          👤 $POSTGRES_USER"
echo -e "          🔑 $POSTGRES_PASSWORD"
echo ""

cd $ROOT_DIR
# remove exported variables from shell
fresh_shell
