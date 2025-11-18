#!/bin/bash

# HOW TO USE
# Inside the docker/ directory, run:
# sudo bash docker.sh <start|stop|restart|update|build>

set -e

DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# initialize the .env files and data folder permissions on first initialization
bash "$DOCKER_DIR"/init.sh

container=${2:-""}

build_containers() {
    docker compose build "$container"
}

stop_containers() {
    docker compose down "$container"
}

start_containers() {
    docker compose up -d "$container"
}

update_containers() {
    git pull
    build_containers "$container"
}

log_containers() {
    docker compose logs -f "$container"
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
    log)
        log_containers
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|update|build|log} [container_name]"
        exit 1
esac

# TODO add more echo and interactivity to let the user know what is happening
