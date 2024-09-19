DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$DOCKER_DIR")"

# TODO add more echo and interactivity to let the user know what is happening

source "$APP_ROOT"/scripts/functions.sh

# if ../app/config/.env does not exist, create it
if [ ! -f "$APP_ROOT"/app/config/.env ]; then
    cp "$APP_ROOT"/app/config/.env.template "$APP_ROOT"/app/config/.env
    update_env "$APP_ROOT"/app/config/.env
fi

# if ../cantaloupe/.env does not exist, create it
if [ ! -f "$APP_ROOT"/cantaloupe/.env ]; then
    # TODO fix that part that is not working correctly
    cp "$APP_ROOT"/cantaloupe/.env.template "$APP_ROOT"/cantaloupe/.env
    update_cantaloupe_env
    bash "$APP_ROOT"/cantaloupe/init.sh
fi

# if docker/.env does not exist, create it
if [ ! -f "$APP_ROOT"/docker/.env ]; then
    cp "$APP_ROOT"/docker/.env.template "$APP_ROOT"/docker/.env
    update_env "$APP_ROOT"/docker/.env
fi

# if app/logs/app_log.log does not exist, create it
if [ ! -f "$APP_ROOT"/logs/app_log.log ]; then
    touch "$APP_ROOT"/logs/app_log.log
    touch "$APP_ROOT"/logs/download.log
    touch "$APP_ROOT"/logs/iiif.log
    chown -R "$USERID:$USERID" "$APP_ROOT"/logs
fi

source "$APP_ROOT"/app/config/.env
source "$APP_ROOT"/docker/.env

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER"/mediafiles ]; then
    cp -r "$APP_ROOT"/app/mediafiles "$DATA_FOLDER"/
    chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

if [ ! -d "$DATA_FOLDER"/sas ]; then
    mkdir -p "$DATA_FOLDER"/sas
    chown -R "$USERID":"$USERID" "$DATA_FOLDER"/sas
fi

# if nginx_conf does not exist, create it
if [ ! -f "$APP_ROOT"/docker/nginx_conf ]; then
    cp "$APP_ROOT"/docker/nginx.conf.template "$APP_ROOT"/docker/nginx_conf
    source "$APP_ROOT"/app/config/.env

    sed -i -e "s~DJANGO_PORT~$DJANGO_PORT~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~NGINX_PORT~$NGINX_PORT~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~SAS_PORT~$SAS_PORT~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~PROD_URL~$PROD_URL~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~SSL_CERTIFICATE~$SSL_CERTIFICATE~" "$APP_ROOT"/docker/nginx_conf
    sed -i -e "s~SSL_KEY~$SSL_KEY~" "$APP_ROOT"/docker/nginx_conf
fi

# TODO redis password
