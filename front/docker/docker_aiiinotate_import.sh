#!/usr/bin/env bash

# this script imports AnnotationLists from a directory
# in an aiiinotate instance. the directory must only contain
# AnnotationLists, with all files at the root of the directory.
#
# USAGE: bash docker_aiiinotate_import.sh <path/to/directory>

# directory containing all files we want to import into aiiinotate
HOST_DIR=$(echo "$1" | sed -e "s~/$~~g")  # sed removes trailing "/"

CONTAINER="docker-aiiinotate-1"

EXEC="docker exec $CONTAINER"
EXEC_IT="docker exec -it $CONTAINER"
NODE_BIN=$($EXEC realpath node_modules/.bin)
NPM_BIN=$($EXEC realpath /usr/local/bin/npm)
DOTENVX_BIN=$($EXEC realpath $NODE_BIN/dotenvx)
AIIINOTATE_BIN=$($EXEC realpath $NODE_BIN/aiiinotate)

# .env file in container.
CONTAINER_ENV_FILE=$($EXEC realpath .env)
# directory where files in $IMPORT_DIR will be stored in the container.
CONTAINER_DIR="import_files"
# file listing absolute paht to contents of $CONTAINER_DIR
CONTAINER_INDEX_FILE=import_files.txt

[ ! -d "$HOST_DIR" ] && {
    echo "import directory '$HOST_DIR' not found ! exiting";
    exit 1
}

# recreate CONTAINER_DIR
$EXEC bash -c "[ -d \"$CONTAINER_DIR\" ] && rm -rf \"$CONTAINER_DIR\"";
$EXEC mkdir "$CONTAINER_DIR"

# covert paths to abspath
CONTAINER_DIR=$($EXEC realpath "$CONTAINER_DIR")
CONTAINER_INDEX_FILE=$($EXEC realpath "$CONTAINER_INDEX_FILE")

# copy all files in $HOST_DIR to the docker in $CONTAINER_DIR.
# if a file in $HOST_DIR is not found, exit.
for fp in "$HOST_DIR"/*; do
    [ ! -f "$fp" ] && {
        echo "file not found on host: '$fp'. exiting.";
        exit 1
    }
    docker container cp "$fp" "$CONTAINER":"$CONTAINER_DIR"
done

$EXEC bash -c "echo \$(find \"$CONTAINER_DIR\"/* -type f | xargs readlink -f > import_files.txt)"
$EXEC cat "$CONTAINER_INDEX_FILE"

$EXEC bash -c \
    "$DOTENVX_BIN run -f \"$CONTAINER_ENV_FILE\" -- \
    \"$AIIINOTATE_BIN\" import -i 2 -f \"$CONTAINER_INDEX_FILE\""

