#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR"/functions.sh

install_packages() {
    if [ "$OS" = "Linux" ]; then
        wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
        sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
        sudo apt update
        sudo apt-get install wget ca-certificates
        sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
    elif [ "$OS" = "Mac" ]; then
        brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript
        brew services start postgresql
        brew services start redis
    else
        color_echo red "Unsupported OS: $OS"
        exit 1
    fi
}

echo_title "SYSTEM PACKAGES INSTALL"
install_packages
