CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$CURRENT_DIR")"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$DOCKER_DIR/.env"
source "$FRONT_ROOT/app/config/.env"

TIMESTAMP=$(date +%Y-%m-%d_%H:%M)

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=$POSTGRES_DB
DB_USER=$POSTGRES_USER
DB_PASSWORD=$POSTGRES_PASSWORD

SQL_DUMP="$DATA_BACKUP/aikon_db_dump_$TIMESTAMP.sql"

if [ "$DATA_BACKUP" = "" ]; then
    read -p "Enter the path where to create backup: " TARGET_FOLDER
fi

if [ ! -d "$DATA_BACKUP" ]; then
    echo "Backup data folder $DATA_BACKUP does not exist. Exiting"
    exit 1
fi

DB_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps -q db)
if [ -z "$DB_CONTAINER" ]; then
   echo "Error: Database container is not running"
   exit 1
fi

# PGPASS_FILE="./.pgpass"
# echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USER:$DB_PASSWORD" > "$PGPASS_FILE"
# chmod 600 "$PGPASS_FILE"
# export PGPASSFILE='./.pgpass'

# docker exec -it $DB_CONTAINER pg_dump -U $DB_USER > "$SQL_DUMP"
# docker cp $DB_CONTAINER:"$SQL_DUMP" "$DATA_BACKUP"

docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -h localhost \
  -p "$DB_PORT" \
  -F p > "$BACKUP_FILE"

# find "$BACKUP_DIR" -name "aikon_db_dump_*.sql*" -type f -mtime +7 -delete
# echo "Old backups (older than 7 days) removed"

# Import SQL data
# docker volume rm docker_pgdata
# docker cp $DB_CONTAINER $SQL_DUMP ./
# docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < $SQL_DUMP
