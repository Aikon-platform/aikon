#!/bin/bash

# HOW TO USE
# Inside the docker/ directory, run:
# sudo bash docker.sh <start|stop|restart|update|build>

set -e

DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# if the .env file does not exist, meaning that docker was never initialized
if [ ! -f "$DOCKER_DIR"/.env ]; then
    bash "$DOCKER_DIR"/init.sh
fi

build_containers() {
    docker compose build
}

stop_containers() {
    docker compose down
}

start_containers() {
    docker compose up -d
}

update_containers() {
    git pull
    build_containers
}

case "$1" in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    restart)
        stop_containers
        start_containers
        ;;
    update)
        stop_containers
        update_containers
        start_containers
        ;;
    build)
        stop_containers
        build_containers
        start_containers
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|update|build}"
        exit 1
esac

# TODO add more echo and interactivity to let the user know what is happening
