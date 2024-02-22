#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# bash import_db.sh database.sql
# You will be asked to enter password twice
# Restart Django to see effects

colorEcho () {
    case "$1" in
        "success") echo -e "\033[32m$2\033[0m";;
        "error") echo -e "\033[31m$2\033[0m";;
        *) echo "$2";;
    esac
}

error () {
    colorEcho "error" "ERROR: $1"
    exit 1
}

db_file=$1

# Load environment variables from .env file
. ../app/config/.env

username=${DB_USERNAME:-admin}

# check if the database $DB_NAME already exists, if so, drop it
#sudo -u postgres psql -c "DROP DATABASE $DB_NAME"

# create database
sudo -i -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -i -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $username;"

# import sql data
psql -h localhost -d "$DB_NAME" -U "$username" -f "$db_file" || error "Failed to import production data"

# Empty migration directory and create new migrations
#find ../app/webapp/migrations -type f ! -name '__init__.py' ! -name 'init.py' -delete
#../venv/bin/python ../app/manage.py makemigrations || error "Failed to create new migrations"

# Update database schema with new migrations
#../venv/bin/python ../app/manage.py migrate || error "Failed to apply new model to database"

# create superuser
#../venv/bin/python ../app/manage.py createsuperuser --username="$username" --email="$CONTACT_MAIL"

#../venv/bin/python ../app/manage.py runserver localhost:8000
