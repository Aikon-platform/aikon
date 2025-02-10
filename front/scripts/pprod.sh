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

#create_db() {
#    user_exists=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER'")
#    if [ "$user_exists" != "1" ]; then
#        sudo -u postgres psql -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
#        sudo -u postgres psql -c "ALTER ROLE $POSTGRES_USER SET client_encoding TO 'utf8';"
#        sudo -u postgres psql -c "ALTER ROLE $POSTGRES_USER SET default_transaction_isolation TO 'read committed';"
#        sudo -u postgres psql -c "ALTER ROLE $POSTGRES_USER SET timezone TO 'UTC';"
#    fi
#    sudo -u postgres psql -c "CREATE DATABASE $POSTGRES_DB;"
#    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"
#}
#
#check_dbname() {
#    db_name=$1
#    count=2
#    while psql -lqt | cut -d \| -f 1 | grep -qw "$db_name"; do
#        db_name="${1}_$count"
#        ((count++))
#    done
#    sed -i "s~^POSTGRES_DB=.*~POSTGRES_DB=\"$db_name\"~" "$ENV_FILE"
#    echo "$db_name"
#}
#
#POSTGRES_DB=$(check_dbname "$POSTGRES_DB")
#create_db "$POSTGRES_DB"

#python "$APP_ROOT"/app/manage.py makemigrations
#python "$APP_ROOT"/app/manage.py migrate
#python "$APP_ROOT"/app/manage.py createsuperuser
python "$APP_ROOT"/app/manage.py collectstatic

sudo chmod 755 "$APP_ROOT/app/logs/app_log.log"
setfacl -m group:"$APP_NAME":rwx "$APP_ROOT/app/logs/app_log.log"

GUNICORN="gunicorn"

configure_nginx() {
    SSL_FILE=/etc/nginx/sites-available/"$APP_NAME"_"$GUNICORN"
    sudo cp "$APP_ROOT"/gunicorn/ssl.template "$SSL_FILE"

    sudo sed -i "s|PROD_URL|$PROD_URL|g" "$SSL_FILE"
    sudo sed -i "s|POSTGRES_DB|$POSTGRES_DB|g" "$SSL_FILE"
    sudo sed -i "s/SAS_PORT/$SAS_PORT/g" "$SSL_FILE"
    sudo sed -i "s/CANTALOUPE_PORT/$CANTALOUPE_PORT/g" "$SSL_FILE"
    sudo sed -i "s|APP_ROOT|$APP_ROOT|g" "$SSL_FILE"
    sudo sed -i "s|MEDIA_DIR|$MEDIA_DIR|g" "$SSL_FILE"
    sudo sed -i "s/GUNIAPP/$GUNICORN/g" "$SSL_FILE"

#    ln -s "$SSL_FILE" /etc/nginx/sites-enabled/
#    sudo systemctl reload nginx.service
#    sudo systemctl enable nginx.service
    # https://docs.ansible.com/ansible/latest/collections/cisco/ise/renew_certificate_module.html
}

create_logs() {
    SERVICE_DIR="$1"
    LOGS="$SERVICE_DIR/error.log"
    SDTOUT="$SERVICE_DIR/stdout.log"
    > $LOGS || touch "$LOGS"
    > $SDTOUT || touch "$SDTOUT"

    chmod u+w $LOGS && chmod u+w $SDTOUT
}

reload_service() {
    SERVICE_NAME="$1"
    sudo systemctl daemon-reload
    sudo systemctl start "$SERVICE_NAME.service"
    sudo systemctl enable "$SERVICE_NAME.service"
    sudo systemctl status "$SERVICE_NAME.service"
}

create_service() {
    SERVICE_NAME="$APP_NAME-$1"
    SERVICE_DIR="$APP_ROOT/$1"
    WORKING_DIR="${2:-$SERVICE_DIR}"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

    sudo chmod -R 755 "$SERVICE_DIR"

    create_logs "$SERVICE_DIR"

    chmod +x "$SERVICE_DIR"/start.sh

    if [ -e "$SERVICE_PATH" ]; then
        echo "Service file '$SERVICE_PATH' already exists."
        sudo systemctl stop "$SERVICE_NAME.service"
    else
        echo "# $SERVICE_PATH
            [Unit]
            User=$APP_NAME
            Group=$APP_NAME
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

        echo "Service file '$SERVICE_NAME' created."
    fi

    reload_service "$SERVICE_NAME"
}

# REDIS & CELERY SETUP
# Allow systemd to manage redis
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sudo sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf

#redis-cli -a "$REDIS_PASSWORD"
sudo systemctl restart redis-server
sudo systemctl status redis

create_service celery "$APP_ROOT"
