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

source "$APP_ROOT"/app/config/.env
source "$APP_ROOT"/docker/.env

# if nginx.conf does not exist, create it
if [ ! -f "$APP_ROOT"/docker/nginx.conf ]; then
    cp "$APP_ROOT"/docker/nginx.conf.template "$APP_ROOT"/docker/nginx.conf
    source "$APP_ROOT"/app/config/.env

    sed -i "" -e "s~NGINX_PORT~$NGINX_PORT~" "$APP_ROOT"/docker/nginx.conf
    sed -i "" -e "s~PROD_URL~$PROD_URL~" "$APP_ROOT"/docker/nginx.conf
fi

# TODO redis password

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi
