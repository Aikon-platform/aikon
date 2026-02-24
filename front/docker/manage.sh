#!/bin/env bash

set -e

manage="uv --directory=/home/aikon/app run /home/aikon/app/manage.py"

$manage collectstatic --noinput

$manage makemigrations
$manage migrate

# check if the superuser exists: https://stackoverflow.com/a/29949548
function superuser_exists() {
    cmd="SELECT * FROM auth_user WHERE auth_user.username='$POSTGRES_USER';"
    docker exec \
        docker-db-1 \
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "$cmd" -t \
        | egrep .
}

# create superuser if it doesn't exist
if [ $(superuser_exists | wc -l) -eq 0 ]; then
    export DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_USERNAME="$POSTGRES_USER"
    export DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_EMAIL="$EMAIL_HOST_USER"
    export DJANGO_SUPERUSER_PASSWORD
    DJANGO_SUPERUSER_PASSWORD="$POSTGRES_PASSWORD"
    $manage createsuperuser --noinput
    echo "Super user created:"
    echo -e "          👤 $POSTGRES_USER"
    echo -e "          🔑 $POSTGRES_PASSWORD"
fi;
