#!/bin/bash

###############################
# VALUES TO BE USED BY DOCKER #
#    modify those values to   #
#      match your system      #
###############################

# Machine path where docker will store its /data/ folder
DATA_FOLDER=/media/aikon/
# User ID to be used by docker
DEMO_UID=1000
# Exposed port
PORT=8001

# Container name
CONTAINER_NAME="aikon"
# Port used inside the container
DOCKER_PORT=PORT


DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$DOCKER_DIR")"

source "$APP_ROOT"/scripts/functions.sh

# TODO update nginx conf with domain name

# if ../app/config/.env does not exist, create it
if [ ! -f "$APP_ROOT"/app/config/.env ]; then
    cp "$APP_ROOT"/app/config/.env.template "$APP_ROOT"/app/config/.env
    update_env "$APP_ROOT"/app/config/.env
fi

# if ../app/cantaloupe/.env does not exist, create it
if [ ! -f "$APP_ROOT"/app/cantaloupe/.env ]; then
    cp "$APP_ROOT"/app/cantaloupe/.env.template "$APP_ROOT"/app/cantaloupe/.env
    update_cantaloupe_env
    bash "$APP_ROOT"/cantaloupe/init.sh
fi

build_container() {
    docker build --rm -t "$CONTAINER_NAME" . -f Dockerfile --build-arg USERID=$DEMO_UID
}

if docker ps -a --format '{{.Names}}' | grep -Eq "^$CONTAINER_NAME$"; then
    docker rm -f "$CONTAINER_NAME"
fi

if [ "$1" = "build" ] || [ "$1" = "update" ]; then
    [ "$1" = "update" ] && git pull
    build_container
fi

# Run Docker container
docker run -d --name "$CONTAINER_NAME" \
   -v "$DATA_FOLDER":/data/ \
   -p $PORT:$DOCKER_PORT -p 8182:8182 -p 8888:8888 \
   --restart unless-stopped --ipc=host "$CONTAINER_NAME"
