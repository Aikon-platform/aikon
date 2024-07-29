#! /bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

read -s -p "Enter your sudo password: " password
echo

(trap 'kill 0' SIGINT;
    (venv/bin/celery -A app.config.celery worker -B -c 1 --loglevel=DEBUG -P threads) &
    (venv/bin/python app/manage.py runserver localhost:8000) &
    (echo "$password" | sudo -S java -Dcantaloupe.config="$ROOT_DIR"/cantaloupe/cantaloupe.properties -Xmx2g -jar "$ROOT_DIR"/cantaloupe/cantaloupe-4.1.11.war > /dev/null 2>&1) &
    (cd "$ROOT_DIR"/sas/ && mvn jetty:run -q);
)
