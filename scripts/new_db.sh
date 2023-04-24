#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# sh new_db.sh dbName

# Load environment variables from .env file
. ../vhs-platform/vhs/.env

dbname=${1:-${DB_NAME}_2}
username=${DB_USERNAME:-admin}

# check if the database $dbname already exists, if so, drop it
sudo -i -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$dbname'" | grep -q 1 && sudo -u postgres psql -c "DROP DATABASE $dbname"

sudo -i -u postgres psql -c "GRANT ALL ON SCHEMA public TO $username;"
sudo -i -u postgres psql -c "GRANT ALL ON SCHEMA public TO public;"
sudo -i -u postgres psql -c "CREATE DATABASE $dbname;"
sudo -i -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $dbname TO $username;"

# Set variables in .env file
sed -i "s/DB_NAME=.*/DB_NAME=$dbname/" ../vhs-platform/vhs/.env

# Empty migration directory and create new migrations
find ../vhs-platform/vhsapp/migrations -type f ! -name '__init__.py' -delete
../venv/bin/python ../vhs-platform/manage.py makemigrations

# Update database schema with new migrations
../venv/bin/python ../vhs-platform/manage.py migrate
