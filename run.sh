#! /bin/bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Prompt the user for a password
read -s -p "Enter your password: " password
echo

(trap 'kill 0' SIGINT;
    python app/manage.py runserver localhost:8000 &

    echo "$password" | sudo -S java -Dcantaloupe.config=$ROOT_DIR/cantaloupe/cantaloupe.properties -Xmx2g -jar $ROOT_DIR/cantaloupe/cantaloupe-4.1.11.war &

    (cd sas/ && mvn jetty:run);
)
