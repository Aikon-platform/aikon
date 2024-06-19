#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# bash new_db.sh <dbName> <?sql_script>
# You will be asked to enter password twice
# Restart Django to see effects

get_os() {
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     os=Linux;;
        Darwin*)    os=Mac;;
        CYGWIN*)    os=Cygwin;;
        MINGW*)     os=MinGw;;
        MSYS_NT*)   os=Git;;
        *)          os="UNKNOWN:${unameOut}"
    esac
    echo "${os}"
}

case $(get_os) in
    Linux)
        command="sudo -i -u postgres psql"
        ;;
    Mac)
        command="psql postgres"
        ;;
    *)
        echo "Unsupported OS: you need to create the database manually"
        exit 1
        ;;
esac

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

db_name=${1:-${DB_NAME}_2}
db_sql_file=$2
db_user=${DB_USERNAME:-admin}
db_psw=${DB_PASSWORD:-dummy_password}

create_user() {
     $command -c "CREATE USER $db_user WITH PASSWORD '$db_psw';"
     $command -c "ALTER ROLE $db_user SET client_encoding TO 'utf8';"
     $command -c "ALTER ROLE $db_user SET default_transaction_isolation TO 'read committed';"
     $command -c "ALTER ROLE $db_user SET timezone TO 'UTC';"
     $command -c "GRANT ALL ON SCHEMA public TO $db_user;"
     $command -c "GRANT ALL ON SCHEMA public TO public;"
}

# check if the user $db_user already exists, if not, create it
is_user=$($command -tc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" | awk '{$1=$1;print}')
if [ "$is_user" != "1" ]; then
    create_user
fi

# check if the database $db_name already exists, if so, drop it
is_db=$($command -tc "SELECT 1 FROM pg_database WHERE datname='$db_name'" | awk '{$1=$1;print}')
if [ "$is_db" == "1" ]; then
    $command -c "DROP DATABASE $db_name;"
fi

$command -c "CREATE DATABASE $db_name;"
$command -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"
$command -c "ALTER DATABASE $db_name OWNER TO $db_user;"

# Set variables in .env file
sed -i '' -e "s/DB_NAME=.*/DB_NAME=$db_name/" "$APP_ROOT"/app/config/.env

if [ -z "$db_sql_file" ]; then
    # Empty migration directory and create new migrations
    # find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' ! -name 'init.py' -delete
    "$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations

    # Update database schema with new migrations
    "$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate

    # create superuser
    "$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py createsuperuser --username="$db_user" --email="$CONTACT_MAIL"
    #echo "from django.contrib.auth.models import User; User.objects.create_superuser('$db_user', '$CONTACT_MAIL', '$DB_PASSWORD')" | "$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py shell
else
    psql -h localhost -d "$db_name" -U "$db_user" -f "$db_sql_file" || echo "‼️ Failed to import SQL data ‼️"
fi
