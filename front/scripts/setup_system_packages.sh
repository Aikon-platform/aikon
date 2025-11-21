#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR"/utils.sh

# float arithmetic comparison is not supported by bash and we need to use `bc`
# usage: if float_comparison "a >= b"; then... ; fi
float_comparison () {
    expr="$1"
    (( $(echo "$expr" |bc -l) ));
}

# mongo install guide: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/#std-label-install-mdb-community-ubuntu
install_mongodb_ubuntu () {

    if [ "$(arch)" != "x86_64" ];
    then echo "MongoDB only supports x86_64 architectures (yours is $(arch)). exiting..."; exit 1
    fi;

    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
        sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

    # fetch the release name. Mongo only supports LTS versions, so if the user's Ubuntu version is not LTS, we get the name of the last LTS released before the user's version.
    source "/etc/lsb-release"
    if float_comparison "$DISTRIB_RELEASE >= 24.04";
    then DISTRIB="noble";
    elif float_comparison  "$DISTRIB_RELEASE >= 22.04";
    then DISTRIB="jammy";
    elif float_comparison "$DISTRIB_RELEASE >= 20.04";
    then DISTRIB="focal";
    else echo "Your Ubuntu version ($DISTRIB_RELEASE) is not supported by MongoDB 8.0"; exit 1;
    fi;

    # create list file
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $DISTRIB/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

    sudo apt-get update
    sudo apt-get install -y mongodb-org
}

install_mongodb_mac () {
    xcode-select --install;
    brew tap mongodb/brew;
    brew update;
    brew install mongodb-community@8.0;
}

install_mongodb() {
    if [ "$OS" = "Linux" ]; then
        install_mongodb_ubuntu;
        sudo systemctl start mongod;
    elif [ "$OS" = "Mac" ]; then
        install_mongodb_mac;
        brew services start mongodb-community@8.0;
    else echo "Unsupported OS: $OS"; exit 1;
    fi;
}

install_packages() {
    if [ "$OS" = "Linux" ]; then
        wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
        sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
        sudo apt update
        sudo apt-get install wget ca-certificates
        sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript libmagic1 gnupg
    elif [ "$OS" = "Mac" ]; then
        brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript libmagic
        brew services start postgresql
        brew services start redis
    else
        color_echo red "Unsupported OS: $OS"
        exit 1
    fi
}

echo_title "SYSTEM PACKAGES INSTALL"
install_packages
install_mongodb
services_start
