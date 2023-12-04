SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

ENV_FILE="$APP_ROOT"/app/config/.env

# Load environment variables
. "$ENV_FILE"

GUNICORN="gunicorn"
GUNIAPP="$APP_NAME-$GUNICORN"

configure_nginx() {
    SSL_FILE=/etc/nginx/sites-available/"$APP_NAME"_"$GUNICORN"
    sudo cp "$SCRIPT_DIR"/ssl.template "$SSL_FILE"

    sudo sed -i "s|PROD_URL|$PROD_URL|g" "$SSL_FILE"
    sudo sed -i "s|DB_NAME|$DB_NAME|g" "$SSL_FILE"
    sudo sed -i "s/SAS_PORT/$SAS_PORT/g" "$SSL_FILE"
    sudo sed -i "s/CANTALOUPE_PORT/$CANTALOUPE_PORT/g" "$SSL_FILE"
    sudo sed -i "s|APP_ROOT|$APP_ROOT|g" "$SSL_FILE"
    sudo sed -i "s|MEDIA_DIR|$MEDIA_DIR|g" "$SSL_FILE"
    sudo sed -i "s/GUNIAPP/$GUNIAPP/g" "$SSL_FILE"

    ln -s "$SSL_FILE" /etc/nginx/sites-enabled/
    sudo systemctl reload nginx.service
    sudo systemctl enable nginx.service
    # https://docs.ansible.com/ansible/latest/collections/cisco/ise/renew_certificate_module.html
    # TODO add $USER to role renew_certif ansible + add file web group to /etc/ansible/hosts
}

configure_nginx

create_service() {
    SERVICE_NAME=$GUNIAPP
    SERVICE_DIR="$APP_ROOT/$1"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

    sudo chmod -R 755 "$SERVICE_DIR"

    LOGS="$SERVICE_DIR/error.log"
    SDTOUT="$SERVICE_DIR/stdout.log"
    > $LOGS || touch "$LOGS"
    > $SDTOUT || touch "$SDTOUT"

    sudo chmod a+rw "$LOGS"
    sudo chmod a+rw "$SDTOUT"
    sudo chmod o+rx "$SERVICE_DIR"/start.sh

    if [ -e "$SERVICE_PATH" ]; then
        echo "Service file '$SERVICE_PATH' already exists."
        sudo systemctl stop "$SERVICE_NAME.service"
    else
        sudo echo "# $SERVICE_PATH
              [Unit]
              Description=gunicorn daemon for $APP_NAME
              Requires=$SERVICE_NAME.socket
              After=network.target

              [Service]
              WorkingDirectory=$APP_ROOT
              ExecStart=$SERVICE_DIR/start.sh
              StandardError=append:$LOGS
              Restart=always

              [Install]
              WantedBy=multi-user.target" | sudo tee "$SERVICE_PATH" > /dev/null
              # StandardOutput=file:$SDTOUT
              # User=$APP_NAME
              # Group=$APP_NAME

        echo "Service file '$SERVICE_NAME' created."
    fi

    sudo systemctl daemon-reload

    sudo systemctl start "$SERVICE_NAME.socket"
    sudo systemctl enable "$SERVICE_NAME.socket"
    sudo systemctl start "$SERVICE_NAME.service"
    sudo systemctl enable "$SERVICE_NAME.service"

    sudo systemctl status "$SERVICE_NAME.service"
    sudo systemctl status "$SERVICE_NAME.socket"
}

create_socket() {
    SOCKET_NAME=$GUNIAPP
    SOCKET_PATH="/etc/systemd/system/$SOCKET_NAME.socket"

    if [ -e "$SOCKET_PATH" ]; then
        echo "Socket file '$SOCKET_PATH' already exists."
        sudo systemctl stop "$SOCKET_NAME.socket"
    else
        echo "# $SOCKET_PATH
              [Unit]
              Description=Gunicorn socket for $APP_NAME

              [Socket]
              ListenStream=/run/$SOCKET_NAME.sock

              [Install]
              WantedBy=sockets.target" | sudo tee "$SOCKET_PATH" > /dev/null

        echo "Service file '$SOCKET_NAME' created."
    fi
}

create_socket $GUNICORN
create_service $GUNICORN
