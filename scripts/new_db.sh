#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# sh new_db.sh

# Load environment variables from .env file
. ../vhs-platform/vhs/.env

dbname=${DB_NAME}_2
username=${DB_USERNAME:-admin}

sudo -u postgres psql -c "CREATE DATABASE $dbname;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $dbname TO $username;"
sudo -u postgres psql -c "\q"

# Set variables in .env file
sed -i "s/DB_NAME=.*/DB_NAME=$dbname/" ../vhs-platform/vhs/.env

# Empty migration directory and create new migrations
find ../vhs-platform/vhsapp/migrations -type f ! -name '__init__.py' -delete
../venv/bin/python ../vhs-platform/manage.py makemigrations

# Update database schema with new migrations
../venv/bin/python ../vhs-platform/manage.py migrate
