#!/bin/bash

DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# if the .env file does not exist, meaning that docker was never initialized
if [ ! -f "$DOCKER_DIR"/.env ]; then
    bash "$DOCKER_DIR"/init.sh
fi

build_containers() {
    docker-compose build
}

if [ "$1" = "build" ] || [ "$1" = "update" ]; then
    [ "$1" = "update" ] && git pull
    build_containers
fi

docker-compose up -d
