# Script to import existing data into Docker database and use existing annotations for SAS container
DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

bash "$DOCKER_DIR/docker.sh" stop

# DATABASE
# take existing env file as script parameter
# extract DB information
# dump DB_NAME with credentials
# docker cp DUMP_FILE aikon_db_1:/tmp/
# docker exec -it aikon_db_1 pg_restore -U POSTGRESUSER -d DB_NAME -c /tmp/DUMP_FILE
# The -c flag will clean (drop) database objects before recreating them. This ensures a clean import.

# MEDIAFILES
# in the env file, check mediafiles path
# is same as $DATA_FOLDER/mediafiles tip top
# otherwise symlink for /media/docker?

# SAS
# - ${DATA_FOLDER}/sas:/sas/data => fix do define special datafolder for SAS


# restart docker
