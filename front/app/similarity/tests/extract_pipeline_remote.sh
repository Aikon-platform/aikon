#!/bin/env bash

# pipeline to replicate tables from a database in a docker.
# steps: copy the sql script in the docker => run it => copy the output outside of the docker.
# must run on a server with the database in a docker.  tables are extracted using `extract.sql`
# needs the following structure:
# root_dir/
#  |_extract_pipeline_remote.sh  # current script
#  |_extract.sql                 # sql script to run the extraction
#  |_data/
#     |_... # results will be stored here

set -e

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SQL_SCRIPT="$SCRIPTPATH/extract.sql"
ENVPATH="$SCRIPTPATH/.env"

if [ ! -f "$ENVPATH" ]; then
	echo "$ENVPATH file not found. exiting...";
	exit 1;
fi
if [ ! -f "$SQL_SCRIPT" ]; then
	echo "$SQL_SCRIPT  not found. exiting...";
	exit 1;
fi

[ ! -d "$FOLDER_OUT" ] && mkdir "$FOLDER_OUT";

source "$ENVPATH"

sudo docker cp "$SQL_SCRIPT" "$DB_DOCKER":/
sudo docker exec -it "$DB_DOCKER" psql -U "$PG_USER" -d "$PG_DB" -p "$PG_PORT" -f "./extract.sql"  # ./extract.sql = position of the file in the docker.
tgt=$(sudo docker exec "$DB_DOCKER" ls | grep -E "webapp_.*\.csv");  # all outputted csv files, prefixed with "webapp_"
while IFS= read -r f; do
	sudo docker cp "$DB_DOCKER":/"$f" "$FOLDER_OUT";
done <<< "$tgt";
