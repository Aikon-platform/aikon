#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# sh new_db.sh dbName
# You will be asked to enter password twice
# Restart Django to see effects

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

dbname=${1:-${DB_NAME}_2}
username=${DB_USERNAME:-admin}

# check if the database $dbname already exists, if so, drop it
sudo -i -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$dbname'" | grep -q 1 && sudo -u postgres psql -c "DROP DATABASE $dbname"

sudo -i -u postgres psql -c "GRANT ALL ON SCHEMA public TO $username;"
sudo -i -u postgres psql -c "GRANT ALL ON SCHEMA public TO public;"
sudo -i -u postgres psql -c "CREATE DATABASE $dbname;"
sudo -i -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $dbname TO $username;"

# Set variables in .env file
sed -i '' -e "s/DB_NAME=.*/DB_NAME=$dbname/" "$APP_ROOT"/app/config/.env

# Empty migration directory and create new migrations
# find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' ! -name 'init.py' -delete
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations

# Update database schema with new migrations
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate

# create superuser
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py createsuperuser --username=$username --email="$CONTACT_MAIL"
