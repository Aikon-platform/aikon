#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$APP_ROOT"/app/config/.env

# Load environment variables
. "$ENV_FILE"

# Requirements
sudo apt update
sudo apt-get install -y wget ca-certificates
sudo apt-get install -y python3-venv python3-dev libpq-dev nginx curl maven postgresql git build-essential poppler-utils redis-server ghostscript

# Set up virtual environment
python3 -m venv venv
source "$APP_ROOT"/venv/bin/activate
pip install -r "$APP_ROOT"/app/requirements-prod.txt

create_db() {
    user_exists=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USERNAME'")
    if [ "$user_exists" != "1" ]; then
        sudo -u postgres psql -c "CREATE USER $DB_USERNAME WITH PASSWORD '$DB_PASSWORD';"
        sudo -u postgres psql -c "ALTER ROLE $DB_USERNAME SET client_encoding TO 'utf8';"
        sudo -u postgres psql -c "ALTER ROLE $DB_USERNAME SET default_transaction_isolation TO 'read committed';"
        sudo -u postgres psql -c "ALTER ROLE $DB_USERNAME SET timezone TO 'UTC';"
    fi
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USERNAME;"
}

check_dbname() {
    db_name=$1
    count=2
    while psql -lqt | cut -d \| -f 1 | grep -qw "$db_name"; do
        db_name="${1}_$count"
        ((count++))
    done
    sed -i "s~^DB_NAME=.*~DB_NAME=\"$db_name\"~" "$ENV_FILE"
    echo "$db_name"
}

DB_NAME=$(check_dbname "$DB_NAME")
create_db "$DB_NAME"

python "$APP_ROOT"/app/manage.py makemigrations
python "$APP_ROOT"/app/manage.py migrate
python "$APP_ROOT"/app/manage.py createsuperuser
python "$APP_ROOT"/app/manage.py collectstatic

create_service() {
    SERVICE_NAME="$APP_NAME-$1"
    SERVICE_DIR="$APP_ROOT/$1"
    WORKING_DIR="${$2:-$SERVICE_DIR}"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

    if [ -e "$SERVICE_PATH" ]; then
        echo "Service file '$SERVICE_PATH' already exists."
    else
        echo "# $SERVICE_PATH
              [Unit]
              Description=$APP_NAME $1 service
              After=network.target
              After=nginx.service

              [Service]
              User=$APP_NAME
              Group=$APP_NAME
              WorkingDirectory=$WORKING_DIR
              ExecStart=$SERVICE_DIR/start.sh
              StandardOutput=file:$SERVICE_DIR/stdout
              StandardError=append:$SERVICE_DIR/log
              Restart=always

              [Install]
              WantedBy=multi-user.target"

        echo "Service file '$SERVICE_NAME' created."
    fi

    sudo systemctl daemon-reload
    sudo systemctl start "$SERVICE_NAME.service"
    sudo systemctl enable "$SERVICE_NAME.service"
    sudo systemctl status "$SERVICE_NAME.service"
}

# NGINX & GUNICORN SET UP
chmod +x "$APP_ROOT"/gunicorn/init.sh
"$APP_ROOT"/gunicorn/init.sh

# CANTALOUPE SET UP
chmod +x "$APP_ROOT"/cantaloupe/init.sh && chmod +x "$APP_ROOT"/cantaloupe/start.sh
"$APP_ROOT"/cantaloupe/init.sh
create_service cantaloupe

# SAS SET UP
chmod +x "$APP_ROOT"/sas/start.sh
create_service sas

# TODO add authentication for SAS
# sudo sh -c "echo -n '$SAS_USERNAME:$SAS_PASSWORD' >> /etc/nginx/.htpasswd"
# + Uncomment 2 "auth_basic" lines in gunicorn/ssl.template

# REDIS & CELERY SETUP
vi /etc/redis/redis.conf
redis-cli -a "$REDIS_PASSWORD"

create_service celery "$APP_ROOT/app"

#
## Restart Nginx
#sudo systemctl restart nginx
#
## Create service for Celery
#vi /etc/systemd/system/celery.service
## Add Celery service configuration
## Save and exit
#
## Reload systemd manager configuration
#sudo systemctl daemon-reload
#
## Enable authentication for Redis instance
#vi /etc/redis/redis.conf
## Uncomment and set a password
## Save and exit
#sudo systemctl restart redis-server
#
#echo "Deployment completed successfully."
