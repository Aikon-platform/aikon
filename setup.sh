#!/bin/bash

AIKON_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/aikon" >/dev/null 2>&1 && pwd )"
DISCOVER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/discover-api" >/dev/null 2>&1 && pwd )"

AIKON_SETUP="$AIKON_DIR/scripts/setup.sh"
DISCOVER_SETUP="$DISCOVER_DIR/setup.sh"

git submodule init
git submodule update

colorEcho() {
    Color_Off="\033[0m"
    Red="\033[1;91m"        # Red
    Green="\033[1;92m"      # Green
    Blue="\033[1;94m"       # Blue
    Purple="\033[1;95m"     # Purple

    case "$1" in
        "green") echo -e "$Green$2$Color_Off";;
        "red") echo -e "$Red$2$Color_Off";;
        "blue") echo -e "$Blue$2$Color_Off";;
        "purple") echo -e "$Purple$2$Color_Off";;
        *) echo "$2";;
    esac
}

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
(cd "$AIKON_DIR" && bash "$AIKON_SETUP")

if [ $? -ne 0 ]; then
    colorEcho red "AIKON setup encountered an error"
    exit 1
# fi

colorEcho green "Discover installation..."
(cd "$DISCOVER_DIR" && bash "$DISCOVER_SETUP")

if [ $? -ne 0 ]; then
    colorEcho red "Discover setup encountered an error"
    exit 1
fi

# replace CV_API_URL in aikon/.env by localhost:discover-api/.env.dev => $API_DEV_PORT
api_port=$(grep "API_DEV_PORT" "$DISCOVER_DIR/.env.dev" | cut -d'=' -f2)
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