#!/bin/bash
# Script to import database, mediafiles and SAS annotations into Docker containers

set -e

IMPORT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$IMPORT_DIR")"
export TARGET_APP_ROOT="$(dirname "$DOCKER_DIR")"

source "$TARGET_APP_ROOT/scripts/utils.sh"

if [ "$1" != "" ]; then
    SOURCE_APP_ROOT="$1"
else
    read -p "Enter the path to source app root: " SOURCE_APP_ROOT
fi

if [ ! -d "$SOURCE_APP_ROOT" ]; then
    error "The provided directory does not exist: $SOURCE_APP_ROOT"
fi

export SOURCE_ENV_FILE="$SOURCE_APP_ROOT/app/config/.env"
export TARGET_ENV_FILE="$TARGET_APP_ROOT/app/config/.env"
if [ ! -f "$SOURCE_ENV_FILE" ]; then
    error "Environment file not found at $SOURCE_ENV_FILE"
fi

color_echo cyan "Source environment file: $SOURCE_ENV_FILE"
cat "$SOURCE_ENV_FILE"

export DB_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps db --format "{{.Name}}")
export SAS_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps sas --format "{{.Name}}")

# docker must already been build
docker compose -f "$DOCKER_DIR/docker-compose.yml" ps -q | grep -q . || error "Docker container appear to not be build yet"

ask "Do you want to proceed with database dump?"
bash "$IMPORT_DIR/import_database.sh"

ask "Do you want to link existing mediafiles into docker?"
bash "$IMPORT_DIR/import_mediafiles.sh"

ask "Do you want to copy existing SAS annotations into SAS data source?"
bash "$IMPORT_DIR/import_sas.sh"

ask "Do you want to restart all containers?"
bash "$DOCKER_DIR/docker.sh" start
