#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$APP_ROOT"/app/config/.env

# Load environment variables
. "$ENV_FILE"

# Requirements
sudo apt update
pip install --upgrade pip

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

sudo chmod 755 "$APP_ROOT/app/logs/app_log.log"
setfacl -m group:"$APP_NAME":rwx "$APP_ROOT/app/logs/app_log.log"

GUNICORN="gunicorn"
GUNIAPP="$APP_NAME-$GUNICORN"

configure_nginx() {
    SSL_FILE=/etc/nginx/sites-available/"$APP_NAME"_"$GUNICORN"
    sudo cp "$APP_ROOT"/gunicorn/ssl.template "$SSL_FILE"

    sudo sed -i "s|PROD_URL|$PROD_URL|g" "$SSL_FILE"
    sudo sed -i "s|DB_NAME|$DB_NAME|g" "$SSL_FILE"
    sudo sed -i "s/SAS_PORT/$SAS_PORT/g" "$SSL_FILE"
    sudo sed -i "s/CANTALOUPE_PORT/$CANTALOUPE_PORT/g" "$SSL_FILE"
    sudo sed -i "s|APP_ROOT|$APP_ROOT|g" "$SSL_FILE"
    sudo sed -i "s|MEDIA_DIR|$MEDIA_DIR|g" "$SSL_FILE"
    sudo sed -i "s/GUNIAPP/$GUNICORN/g" "$SSL_FILE"

    ln -s "$SSL_FILE" /etc/nginx/sites-enabled/
    sudo systemctl reload nginx.service
    sudo systemctl enable nginx.service
    # https://docs.ansible.com/ansible/latest/collections/cisco/ise/renew_certificate_module.html
    # TODO add $USER to role renew_certif ansible + add file web group to /etc/ansible/hosts
}

create_service() {
    SERVICE_NAME="$APP_NAME-$1"
    SERVICE_DIR="$APP_ROOT/$1"
    WORKING_DIR="${2:-$SERVICE_DIR}"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

    sudo chmod -R 755 "$SERVICE_DIR"

    LOGS="$SERVICE_DIR/error.log"
    SDTOUT="$SERVICE_DIR/stdout.log"
    > $LOGS || touch "$LOGS"
    > $SDTOUT || touch "$SDTOUT"

    chmod +x "$SERVICE_DIR"/start.sh
    chmod u+w $LOGS && chmod u+w $SDTOUT

    if [ -e "$SERVICE_PATH" ]; then
        echo "Service file '$SERVICE_PATH' already exists."
        sudo systemctl stop "$SERVICE_NAME.service"
    else
        echo "# $SERVICE_PATH
            [Unit]
            Description=$APP_NAME $1 service
            After=network.target
            After=nginx.service

            [Service]
            WorkingDirectory=$WORKING_DIR
            ExecStart=$SERVICE_DIR/start.sh
            StandardError=append:$LOGS
            Restart=always

            [Install]
            WantedBy=multi-user.target" | sudo tee "$SERVICE_PATH" > /dev/null
            # User=$APP_NAME
            # Group=$APP_NAME
            # StandardOutput=file:$SDTOUT

        echo "Service file '$SERVICE_NAME' created."
    fi

    sudo systemctl daemon-reload
    sudo systemctl start "$SERVICE_NAME.service"
    sudo systemctl enable "$SERVICE_NAME.service"
    sudo systemctl status "$SERVICE_NAME.service"
}

# REDIS & CELERY SETUP
# Allow systemd to manage redis
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sudo sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf

#redis-cli -a "$REDIS_PASSWORD"
sudo systemctl restart redis-server
sudo systemctl status redis

create_service celery "$APP_ROOT"
