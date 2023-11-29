SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

ENV_FILE="$APP_ROOT"/app/config/.env

# Load environment variables
. "$ENV_FILE"

GUNICORN="gunicorn"
GUNIAPP="$APP_NAME-$GUNICORN"

configure_nginx() {
    SSL_FILE=/etc/nginx/sites-available/"$APP_NAME_$GUNICORN"
    cp "$SCRIPT_DIR"/ssl.template "$SSL_FILE"

    sed -i "s|PROD_URL|$PROD_URL|g" "$SSL_FILE"
    sed -i "s|DB_NAME|$DB_NAME|g" "$SSL_FILE"
    sed -i "s/SAS_PORT/$SAS_PORT/g" "$SSL_FILE"
    sed -i "s/CANTALOUPE_PORT/$CANTALOUPE_PORT/g" "$SSL_FILE"
    sed -i "s|APP_ROOT|$APP_ROOT|g" "$SSL_FILE"
    sed -i "s/MEDIA_DIR/$MEDIA_DIR/g" "$SSL_FILE"
    sed -i "s/GUNIAPP/$GUNIAPP/g" "$SSL_FILE"
}

create_service() {
    SERVICE_NAME=$GUNIAPP
    SERVICE_DIR="$APP_ROOT/$1"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

    if [ -e "$SERVICE_PATH" ]; then
        echo "Service file '$SERVICE_PATH' already exists."
    else
        echo "# $SERVICE_PATH
              [Unit]
              Description=gunicorn daemon for $APP_NAME
              Requires=gunicorn.socket
              After=network.target

              [Service]
              User=$APP_NAME
              Group=$APP_NAME
              WorkingDirectory=$APP_ROOT/app
              ExecStart=$APP_ROOT/venv/bin/gunicorn \
                        --access-logfile $SERVICE_DIR/stdout  \
                        --error-logfile $SERVICE_DIR/log  \
                        --workers 3 \
                        --bind unix:/run/$SERVICE_NAME.sock \
                        --timeout 150 \
                        config.wsgi:application

              [Install]
              WantedBy=multi-user.target"

        echo "Service file '$SERVICE_NAME' created."
    fi

    sudo systemctl daemon-reload
    sudo systemctl start "$SERVICE_NAME.service"
    sudo systemctl enable "$SERVICE_NAME.service"
    sudo systemctl status "$SERVICE_NAME.service"
}

create_socket() {
    SOCKET_NAME=$GUNIAPP
    SOCKET_PATH="/etc/systemd/system/$SOCKET_NAME.socket"

    if [ -e "$SOCKET_PATH" ]; then
        echo "Socket file '$SOCKET_PATH' already exists."
    else
        echo "# $SOCKET_PATH
              [Unit]
              Description=gunicorn socket for $APP_NAME

              [Socket]
              ListenStream=/run/$SOCKET_NAME.sock

              [Install]
              WantedBy=sockets.target"

        echo "Service file '$SOCKET_NAME' created."
    fi

    sudo systemctl daemon-reload
    sudo systemctl start "$SOCKET_NAME.socket"
    sudo systemctl enable "$SOCKET_NAME.socket"
    sudo systemctl status "$SOCKET_NAME.socket"

    # Troubleshooting: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04#checking-for-the-gunicorn-socket-file
}

create_socket $GUNICORN
create_service $GUNICORN
