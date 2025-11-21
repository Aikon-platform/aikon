#!/bin/env bash

# mongo install guide: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/#std-label-install-mdb-community-ubuntu

#NOTE only the mongodb installation is done here. for database creation, see `setup_mongodb_populate.sh`

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh";

install_mongodb_ubuntu () {

    sudo apt-get install gnupg curl

    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
    sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg \
    --dearmor

    # assert we have an 86 64 architecture
    if [ "$(arch)" != "x86_64" ];
    then echo "MongoDB only supports x86_64 architectures (yours is $(arch)). exiting..."; exit 1
    fi;

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

if ! command -v mongod ; then
    echo_title "INSTALL MONGODB"

    if [ "$OS" = "Linux" ]; then
        install_mongodb_ubuntu;
        sudo systemctl start mongod;
    elif [ "$OS" = "Mac" ]; then
        install_mongodb_mac;
        brew services start mongodb-community@8.0;
    else echo "Unsupported OS: $OS"; exit 1;
    fi;

fi;
