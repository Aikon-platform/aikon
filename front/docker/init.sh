DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT/scripts/utils.sh"
export INSTALL_MODE="full_install"

# TODO use aikon-demo check for .env modification

# if docker/.env does not exist, create it
if [ ! -f "$FRONT_ROOT/docker/.env" ]; then
    echo_title "DOCKER ENVIRONMENT VARIABLES"
    setup_env "$DOCKER_DIR/.env"
    export MEDIA_DIR="$DATA_FOLDER/mediafiles"
fi

# if ../app/config/.env does not exist, create it
if [ ! -f "$FRONT_ROOT"/app/config/.env ]; then
    echo_title "DJANGO APP ENVIRONMENT VARIABLES"
    update_app_env "$FRONT_ROOT/app/config/.env"
fi

# if ../cantaloupe/.env does not exist, create it
CANTALOUPE_DIR="$FRONT_ROOT"/cantaloupe
if [ ! -f "$CANTALOUPE_DIR/.env" ]; then
    echo_title "CANTALOUPE SETUP"
    setup_cantaloupe "quick_install"
fi

# if app/logs/app_log.log does not exist, create it
if [ ! -f "$FRONT_ROOT/app/logs/app_log.log" ]; then
    echo_title "LOG FILE CREATION"
    touch "$FRONT_ROOT/app/logs/app_log.log"
    touch "$FRONT_ROOT/app/logs/download.log"
    touch "$FRONT_ROOT/app/logs/iiif.log"
    chown -R "$USERID:$USERID" "$FRONT_ROOT"/app/logs
fi

source "$FRONT_ROOT"/app/config/.env
source "$DOCKER_DIR/.env"

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    echo_title "CREATION OF $DATA_FOLDER"
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER"/mediafiles ]; then
    chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

if [ ! -d "$DATA_FOLDER"/sas ]; then
    mkdir -p "$DATA_FOLDER"/sas
    chown -R "$USERID":"$USERID" "$DATA_FOLDER"/sas
fi

# if nginx.conf does not exist, create it
if [ ! -f "$FRONT_ROOT"/docker/nginx.conf ]; then
    echo_title "NGINX CONFIGURATION"
    NGINX_CONF="$DOCKER_DIR/nginx.conf"
    cp "$NGINX_CONF.template" "$NGINX_CONF"

    sed_repl_inplace "s~DJANGO_PORT~$DJANGO_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~NGINX_PORT~$NGINX_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~SAS_PORT~$SAS_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~DB_PORT~$DB_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~REDIS_PORT~$REDIS_PORT~" "$NGINX_CONF"
    sed_repl_inplace "s~PROD_URL~$PROD_URL~" "$NGINX_CONF"
    sed_repl_inplace "s~SSL_CERTIFICATE~$SSL_CERTIFICATE~" "$NGINX_CONF"
    sed_repl_inplace "s~SSL_KEY~$SSL_KEY~" "$NGINX_CONF"
fi

# TODO redis password
