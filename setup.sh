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

<<<<<<< HEAD
echoTitle(){
    sep_line="========================================"
    len_title=${#1}

    if [ "$len_title" -gt 40 ]; then
        sep_line=$(printf "%0.s=" $(seq 1 $len_title))
        title="$1"
    else
        diff=$((38 - len_title))
        half_diff=$((diff / 2))
        sep=$(printf "%0.s=" $(seq 1 $half_diff))

        if [ $((diff % 2)) -ne 0 ]; then
            title="$sep $1 $sep="
        else
            title="$sep $1 $sep"
        fi
    fi

    colorEcho purple "\n\n$sep_line\n$title\n$sep_line"
}

echoTitle "AIKON BUNDLE INSTALL"

colorEcho green "AIKON installation..."
(cd "$AIKON_DIR" && bash "$AIKON_SETUP")||colorEcho red "FRONT setup encountered an error" && exit 1

colorEcho green "API installation..."
(cd "$API_DIR" && bash "$API_SETUP")||colorEcho red "API setup encountered an error" && exit 1
=======
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
>>>>>>> main

# replace CV_API_URL in aikon/.env by localhost:discover-api/.env.dev => $API_DEV_PORT
api_port=$(grep "API_DEV_PORT" "$API_DIR/.env.dev" | cut -d'=' -f2)
api_url=http://localhost:$(echo "$api_port" | tr -d '"')
sed -i "" -e "s~^CV_API_URL=.*~CV_API_URL=$api_url~" "$AIKON_DIR/app/config/.env"

<<<<<<< HEAD
echoTitle "🎉 SETUP COMPLETE! 🎉"
colorEcho blue "\nYou can now run the app and API with: "
colorEcho green "              bash run.sh"
=======
echo_title "🎉 AIKON & DISCOVER ARE SET UP! 🎉"
color_echo blue "\nYou can now run the app and API with: "
color_echo green "              bash run.sh"
>>>>>>> main

user=$(grep "POSTGRES_USER" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
password=$(grep "POSTGRES_PASSWORD" "$AIKON_DIR/app/config/.env" | cut -d'=' -f2)
color_echo blue '\nConnect to app using:'
echo -e "          👤 $user"
echo -e "          🔑 $password"
