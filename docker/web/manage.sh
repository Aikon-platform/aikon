#!/bin/env bash

set -e

ENV_PATH="/home/aikon/app/config/.env"
source "$ENV_PATH"

# function to print an error log if connection to the database fails.
# the most probable error case is that a previous user was created with
# a different password => suggest a fix
psql_error_log () {
    error_log="$1"
    env_contents="$(cat "$ENV_PATH")"

    cat <<EOF
❌ ERROR when connecting to database !

📜 full error log:
$error_log

🗝️ .env used to connect to the database:
$env_contents

⚠️ this is likely due to a stale database user with a different password.

🔧 to reset the PostgreSQL user password, run:
    docker exec -it aikon-db-1 psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"

exiting...
EOF
    exit 1
}

manage="uv --directory=/home/aikon/app run /home/aikon/app/manage.py"

echo ""
echo "collecting staticfiles..."
$manage collectstatic --noinput
echo "✅ staticfiles collected"

echo ""
echo "running migrations..."
if ! migration_output=$($manage migrate 2>&1); then
    psql_error_log "$migration_output";
fi
echo "✅ migrations completed"

echo ""
echo "creating superuser..."
$manage create_superuser_check
echo "✅ superuser setup completed"
