#!/usr/bin/env bash

# this script imports AnnotationLists from a directory
# in an aiiinotate instance. the directory must only contain
# AnnotationLists, with all files at the root of the directory.
#
# USAGE: bash docker_aiiinotate_import.sh <"annotations"|"manifests"> <path/to/directory>

# "annotation" or "manifest": the type of data to import.
DATATYPE="$1"

# directory containing all files we want to import into aiiinotate
HOST_DIR=$(echo "$2" | sed -e "s~/$~~g")  # sed removes trailing "/"

CONTAINER="docker-aiiinotate-1"

EXEC="docker exec $CONTAINER"
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

[[ "$DATATYPE" != "annotation" && "$DATATYPE" != "manifest" ]] && {
  echo "error: DATATYPE must be 'annotation' or 'manifest' (got: '$DATATYPE')"
  exit 1
}

[ ! -d "$HOST_DIR" ] && {
    echo "error: import directory '$HOST_DIR' not found ! exiting";
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
    \"$AIIINOTATE_BIN\" import \"$DATATYPE\" -i 2 -f \"$CONTAINER_INDEX_FILE\""
