CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$CURRENT_DIR")"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$DOCKER_DIR/.env"
source "$FRONT_ROOT/app/config/.env"

DB_USER="${POSTGRES_USER?Error: POSTGRES_USER must be set in .env}"
DB_PASSWORD="${POSTGRES_PASSWORD?Error: POSTGRES_PASSWORD must be set in .env}"
DB_NAME="${POSTGRES_DB?Error: POSTGRES_DB must be set in .env}"
DB_PORT="${DB_PORT:-5432}"

if [[ ! -d "$DATA_BACKUP" ]]; then
    echo "Error: Backup data directory '$DATA_BACKUP' does not exist."
    echo "Please create it or correct the DATA_BACKUP variable in your .env file."
    exit 1
fi

TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE="$DATA_BACKUP/db_backup_${DB_NAME}_${TIMESTAMP}.dump"

DB_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps -q db)
if [[ -z "$DB_CONTAINER" ]]; then
   echo "Error: Database container is not running or not found"
   exit 1
fi

# PGPASS_FILE="./.pgpass"
# echo "$DB_HOST:$DB_PORT:$DB_NAME:$DB_USER:$DB_PASSWORD" > "$PGPASS_FILE"
# chmod 600 "$PGPASS_FILE"
# export PGPASSFILE='./.pgpass'

# docker exec -it $DB_CONTAINER pg_dump -U $DB_USER > "$SQL_DUMP"
# docker cp $DB_CONTAINER:"$SQL_DUMP" "$DATA_BACKUP"

docker exec \
  -e PGPASSWORD="$DB_PASSWORD" \
  "$DB_CONTAINER" \
  pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -h localhost \
    -p "$DB_PORT" \
    -F c \
    --verbose \
  > "$BACKUP_FILE"

DUMP_STATUS=$?
if [[ $DUMP_STATUS -ne 0 ]]; then
    # remove potentially incomplete backup file
    rm -f "$BACKUP_FILE"
    echo "Error: pg_dump failed with status $DUMP_STATUS." > "$BACKUP_FILE"
    exit
fi

echo "Database backup created at: $BACKUP_FILE"

# # Removing backup older than 7 days
# DAYS_TO_KEEP=7
# find "$DATA_BACKUP" -name "db_backup_*.dump" -type f -mtime +"$DAYS_TO_KEEP" -print -delete
