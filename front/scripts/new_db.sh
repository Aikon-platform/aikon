#!/bin/env bash

# HOW TO USE
# Inside the scripts/ directory, run:
# bash new_db.sh <dbName> <?sql_script>
# You will be asked to enter password twice
# Restart Django to see effects

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/utils.sh

APP_ENV="$APP_ROOT"/app/config/.env
# Load environment variables from .env file
. "$APP_ENV"

if [ "$OS" = "Linux" ]; then
    command="sudo -i -u postgres psql"
elif [ "$OS" = "Mac" ]; then
    command="psql postgres"
else
    color_echo red "Unsupported OS: you need to create the database manually"
    exit 1
fi

# list all databases with
# $command -c '\l'

db_name=${1:-${POSTGRES_DB}_2}
db_sql_file=$2
db_user=${POSTGRES_USER:-admin}
db_psw=${POSTGRES_PASSWORD:-dummy_password}

if [[ "$DOCKER" = "True" ]]; then
    db_host="db"
else
    db_host="localhost"
fi

create_user() {
    sql_arr=( "CREATE USER $db_user WITH PASSWORD '$db_psw';"
              "ALTER USER $db_user CREATEDB;"
              "ALTER ROLE $db_user SET client_encoding TO 'utf8';"
              "ALTER ROLE $db_user SET default_transaction_isolation TO 'read committed';"
              "ALTER ROLE $db_user SET timezone TO 'UTC';"
              "GRANT ALL ON SCHEMA public TO $db_user;"
              "GRANT ALL ON SCHEMA public TO public;" )
    for sql in "${sql_arr[@]}"; do
        $command -c "$sql"
    done;
}

update_user() {
    $command -c "ALTER USER $db_user WITH PASSWORD '$db_psw';"
}

# check if the user $db_user already exists. if it exists, update its pw to match the .env. if it doesn't exist, create it
is_user=$($command -tc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" | xargs)
if [ "$is_user" != "1" ]; then
    create_user
else
    update_user
fi

# check if the database $db_name already exists, if so, drop it
is_db=$($command -tc "SELECT 1 FROM pg_database WHERE datname='$db_name'" | xargs)
if [ "$is_db" == "1" ]; then
    $command -c "DROP DATABASE $db_name;"
fi

$command -c "CREATE DATABASE $db_name;"
$command -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"
$command -c "ALTER DATABASE $db_name OWNER TO $db_user;"

# Set new database name in .env file
sed_repl_inplace "s/POSTGRES_DB=.*/POSTGRES_DB=$db_name/" "$APP_ROOT"/app/config/.env

manage="$APP_ROOT/venv/bin/python $APP_ROOT/app/manage.py"

if [ -z "$db_sql_file" ]; then
    # Empty migration directory
    # find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' ! -name 'init.py' -delete

    # Create new migrations
    $manage makemigrations

    # Update database schema with new migrations
    $manage migrate

    # create superuser
    export DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_USERNAME=$(get_env_value "POSTGRES_USER" "$APP_ENV")
    export DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_EMAIL=$(get_env_value "EMAIL_HOST_USER" "$APP_ENV")
    export DJANGO_SUPERUSER_PASSWORD
    DJANGO_SUPERUSER_PASSWORD=$(get_env_value "POSTGRES_PASSWORD" "$APP_ENV")
    $manage createsuperuser --noinput
    # $manage createsuperuser --username="$db_user" --email="$EMAIL_HOST_USER"
else
    psql -h "$db_host" -d "$db_name" -U "$db_user" -f "$db_sql_file" || echo "‼️ Failed to import SQL data ‼️"
fi

color_echo blue '\nConnect to django app using:'
echo -e "          👤 $db_user"
echo -e "          🔑 $POSTGRES_PASSWORD"
