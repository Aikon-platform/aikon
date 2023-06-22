#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# sh prod_db.sh dbName

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

db_file=$(date +%Y-%m-%d)_dump.sql
current_dir=$(pwd)

ssh -t eida "sh dump_db.sh" || error "Failed dump database"
scp eida:backup/$db_file $current_dir || error "Failed to download database dump file"

# Load environment variables from .env file
. ../app/config/.env

dbname=${1:-${DB_NAME}_2}
username=${DB_USERNAME:-admin}

# check if the database $dbname already exists, if so, drop it
sudo -i -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$dbname'" | grep -q 1 && sudo -u postgres psql -c "DROP DATABASE $dbname"

# create database
sudo -i -u postgres psql -c "CREATE DATABASE $dbname;"
sudo -i -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $dbname TO $username;"

# import production data to local database
psql -h localhost -d $dbname -U $username -f $db_file || error "Failed to import production data"
rm $db_file

# Set variables in .env file
sed -i "s/DB_NAME=.*/DB_NAME=$dbname/" ../app/config/.env

# Empty migration directory and create new migrations
find ../app/webapp/migrations -type f ! -name '__init__.py' -delete
../venv/bin/python ../app/manage.py makemigrations || error "Failed to create new migrations"

# Update database schema with new migrations
../venv/bin/python ../app/manage.py migrate || error "Failed to apply new model to database"
