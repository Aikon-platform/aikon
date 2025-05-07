CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$CURRENT_DIR")"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$DOCKER_DIR/.env"
source "$FRONT_ROOT/app/config/.env"

DB_CONTAINER=$(docker compose -f "$DOCKER_DIR/docker-compose.yml" ps -q db)
if [[ -z "$DB_CONTAINER" ]]; then
   echo "Error: Database container is not running or not found"
   exit 1
fi

docker stop $DB_CONTAINER
LATEST_BACKUP=$(ls -t "$DATA_BACKUP"/db_backup_*.dump | head -n 1)

cat "$LATEST_BACKUP" | docker exec -i \
  -e PGPASSWORD="$POSTGRES_PASSWORD" \
  "$DB_CONTAINER_ID" \
  pg_restore \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --verbose

RESTORE_STATUS=$?
if [[ $RESTORE_STATUS -ne 0 ]]; then
  echo "Error: Restore failed with status $RESTORE_STATUS"
  exit $RESTORE_STATUS
else
  echo "Restore completed successfully."
fi
