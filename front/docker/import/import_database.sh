source "$TARGET_APP_ROOT/scripts/utils.sh"
echo_title "ORIGINAL DATABASE DUMP"
source "$SOURCE_ENV_FILE"

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
echo_title "DOCKER IMPORT DATABASE"

docker start $DB_CONTAINER || error "Failed to start database container"
color_echo yellow "Waiting for DB container to start..."
sleep 10

docker cp "$DUMP_FILE" "$DB_CONTAINER:/tmp/dump.sql" || error "Failed to copy dump file to container"
color_echo yellow "SQL script copied to $DB_CONTAINER:/tmp/dump.sql"

source "$TARGET_ENV_FILE"
docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || color_echo yellow "Schema reset failed, continuing anyway..."
docker exec "$DB_CONTAINER" bash -c "psql -U $POSTGRES_USER -d $POSTGRES_DB < /tmp/dump.sql" || error "Failed to import database"
color_echo yellow "SQL data imported into $DB_CONTAINER"
