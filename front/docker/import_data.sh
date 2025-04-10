#!/bin/bash
# Script to import database, mediafiles and SAS annotations into Docker containers

set -e

DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TARGET_APP_ROOT="$(dirname "$DOCKER_DIR")"

source "$TARGET_APP_ROOT/scripts/utils.sh"
ask() {
    options=("yes" "no")
    color_echo blue "$1"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    if [ "$answer" = "no" ]; then
        exit 1
    fi
}

error() {
    color_echo red "$1"
    exit 1
}

if [ "$1" != "" ]; then
    SOURCE_APP_ROOT="$1"
else
    read -p "Enter the path to source app root: " SOURCE_APP_ROOT
fi

if [ ! -d "$SOURCE_APP_ROOT" ]; then
    error "The provided directory does not exist: $SOURCE_APP_ROOT"
fi

SOURCE_ENV_FILE="$SOURCE_APP_ROOT/app/config/.env"
TARGET_ENV_FILE="$TARGET_APP_ROOT/app/config/.env"
if [ ! -f "$SOURCE_ENV_FILE" ]; then
    error "Environment file not found at $SOURCE_ENV_FILE"
fi

source "$SOURCE_ENV_FILE"
cat "$SOURCE_ENV_FILE"

ask "Do you want to proceed with database dump?"
echo_title "EXISTING DATABASE DUMP"

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=$POSTGRES_DB
DB_USER=$POSTGRES_USER
DB_PASSWORD=$POSTGRES_PASSWORD

DUMP_FILE="/tmp/aikon_db_dump_$(date +%Y-%m-%d_%H:%M).sql"
PGPASS_FILE="/tmp/.pgpass_$TIMESTAMP"
echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USER:$DB_PASSWORD" > "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"
export PGPASSFILE="$PGPASS_FILE"

pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$DUMP_FILE" || error "Failed to dump database"
color_echo yellow "Database dumped to $DUMP_FILE"
rm "$PGPASS_FILE"

ask "Do you want to import database dump into docker?"
echo_title "DOCKER IMPORT EXISTING DATABASE"

# docker must already been build
bash "$DOCKER_DIR/docker.sh" log || error "Docker container appear to not be build yet"

DB_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps db --format "{{.Name}}")
SAS_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps sas --format "{{.Name}}")

docker compose -f up -d $DB_CONTAINER || error "Failed to start database container"
color_echo yellow "Waiting for DB container to start..."
sleep 10
docker cp "$DUMP_FILE" "$DB_CONTAINER:/tmp/dump.sql" || error "Failed to copy dump file to container"
color_echo yellow "SQL script copied to $DB_CONTAINER:/tmp/dump.sql"

docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || color_echo yellow "Schema reset failed, continuing anyway..."
docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "/tmp/dump.sql" || error "Failed to import database"
color_echo yellow "SQL data imported into $DB_CONTAINER"

ask "Do you want to link existing mediafiles into docker?"
echo_title "MEDIAFILES LINKING"
source "$DOCKER_DIR/.env"

DOCKER_ENV_FILE="$DOCKER_DIR/.env"
if [ ! -f "$DOCKER_ENV_FILE" ]; then
    error "Environment file not found at $DOCKER_ENV_FILE"
fi
SOURCE_MEDIA_DIR=$MEDIA_DIR
TARGET_MEDIA_DIR="$DATA_FOLDER/mediafiles"

color_echo cyan "Source media directory: $SOURCE_MEDIA_DIR"
color_echo cyan "Target media directory: $TARGET_MEDIA_DIR"

if [ "$SOURCE_MEDIA_DIR" = "$TARGET_MEDIA_DIR" ]; then
    color_echo yellow "Source and destination media directories match! No need to link."
else
    color_echo yellow "Linking existing media files from $SOURCE_MEDIA_DIR to $TARGET_MEDIA_DIR"
    ln -s "$SOURCE_MEDIA_DIR"/* "$TARGET_MEDIA_DIR"/ || error "Failed to symlink mediafiles/"
    # rsync -av --progress "$SOURCE_MEDIA_DIR/" "TARGET_MEDIA_DIR/" || error "Failed to copy media files"
fi

ask "Do you want to copy existing SAS annotations into SAS data source?"
echo_title "SAS ANNOTATIONS DUPLICATION"

SOURCE_SAS_DIR="$SOURCE_APP_ROOT/sas/data"
if [ ! -d "$SOURCE_SAS_DIR" ]; then
    error "SAS data directory not found at $SOURCE_SAS_DIR"
fi
TARGET_SAS_DIR="$DATA_FOLDER/sas"
if [ ! -d "$TARGET_SAS_DIR" ]; then
    mkdir -p "$TARGET_SAS_DIR" || error "Failed to create SAS data directory"
    chmod 755 "$TARGET_SAS_DIR"
fi

color_echo cyan "Source SAS directory: $SOURCE_SAS_DIR"
color_echo cyan "Target SAS directory: $TARGET_SAS_DIR"

if [ "$SOURCE_SAS_DIR" = "$TARGET_SAS_DIR" ]; then
    color_echo yellow "Source and destination SAS directories match! No need to copy data."
else
    color_echo yellow "Rsyncing existing SAS data from $SOURCE_SAS_DIR to $TARGET_SAS_DIR"
    rsync -av --progress "$SOURCE_SAS_DIR/" "$TARGET_SAS_DIR/" || error "Failed to copy SAS data"
fi

ask "Do you want to check that annotations are well accessed by SAS container?"
docker compose -f up -d $SAS_CONTAINER || error "Failed to start SAS container"
color_echo yellow "Waiting for SAS container to start..."
sleep 10

SAS_VOLUME_FILES=$(ls -A "$TARGET_SAS_DIR" 2>/dev/null | wc -l)
SAS_DOCKER_FILES=$(docker exec -i "$SAS_CONTAINER" ls -A /sas/data 2>/dev/null | wc -l)

if [ ! "$SAS_DOCKER_FILES" -eq "$SAS_VOLUME_FILES" ]; then
    color_echo yellow "Content of SAS container data does not match mounted volume. Copying data into container..."

    TAR_FILE="/tmp/sas_data_$TIMESTAMP.tar"
    tar -cf "$TAR_FILE" -C "$TARGET_SAS_DIR" . || error "Failed to create tar file of SAS data"

    docker cp "$TAR_FILE" "$SAS_CONTAINER:/tmp/sas_data.tar" || error "Failed to copy tar file to container"
    docker exec -i "$SAS_CONTAINER" mkdir -p /sas/data
    docker exec -i "$SAS_CONTAINER" tar -xf /tmp/sas_data.tar -C /sas/data || error "Failed to extract tar file in container"

    rm "$TAR_FILE"
    docker exec -i "$SAS_CONTAINER" rm /tmp/sas_data.tar

    color_echo yellow "SAS data copied to container successfully"
fi

ask "Do you want to restart all containers?"

bash "$DOCKER_DIR/docker.sh" start
sleep 10
bash "$DOCKER_DIR/docker.sh" log
