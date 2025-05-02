DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT/scripts/utils.sh"
export INSTALL_MODE="full_install"

# TODO use aikon-demo check for .env modification

# if ../app/config/.env does not exist, create it
if [ ! -f "$FRONT_ROOT"/app/config/.env ]; then
    echo_title "DJANGO APP ENVIRONMENT VARIABLES"
    update_app_env "$FRONT_ROOT/app/config/.env"
fi
source "$FRONT_ROOT"/app/config/.env

# if docker/.env does not exist, create it
if [ ! -f "$FRONT_ROOT/docker/.env" ]; then
    echo_title "DOCKER ENVIRONMENT VARIABLES"
    # TODO make sure all ports defined in .env are copied to docker/.env
    setup_env "$DOCKER_DIR/.env"
    export MEDIA_DIR="$DATA_FOLDER/mediafiles"
fi
source "$DOCKER_DIR/.env"

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

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    echo_title "CREATION OF $DATA_FOLDER"
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER/mediafiles" ]; then
    mkdir -p "$DATA_FOLDER"/mediafiles
    chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

if [ ! -d "$DATA_FOLDER/sas" ]; then
    mkdir -p "$DATA_FOLDER/sas"
    chown -R "$USERID":"$USERID" "$DATA_FOLDER/sas"
fi

generate_conf() {
    local conf_file="$1"
    cp "$conf_file.template" "$conf_file"

    sed_repl_inplace "s~DJANGO_PORT~$DJANGO_PORT~" "$conf_file"
    sed_repl_inplace "s~NGINX_PORT~$NGINX_PORT~" "$conf_file"
    sed_repl_inplace "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~" "$conf_file"
    sed_repl_inplace "s~SAS_PORT~$SAS_PORT~" "$conf_file"
    sed_repl_inplace "s~DB_PORT~$DB_PORT~" "$conf_file"
    sed_repl_inplace "s~REDIS_PORT~$REDIS_PORT~" "$conf_file"
    sed_repl_inplace "s~PROD_URL~$PROD_URL~" "$conf_file"
    sed_repl_inplace "s~SSL_CERTIFICATE~$SSL_CERTIFICATE~" "$conf_file"
    sed_repl_inplace "s~SSL_KEY~$SSL_KEY~" "$conf_file"
    sed_repl_inplace "s~NGINX_MAX_BODY_SIZE~$NGINX_MAX_BODY_SIZE~" "$conf_file"
    sed_repl_inplace "s~NGINX_TIMEOUT~$NGINX_TIMEOUT~" "$conf_file"
}

# if nginx.conf does not exist, create it
if [ ! -f "$DOCKER_DIR/nginx.conf" ]; then
    echo_title "GENERATE NGINX CONFIGURATION"
    generate_conf "$DOCKER_DIR/nginx.conf"
    generate_conf "$DOCKER_DIR/nginx_external.conf"
    generate_conf "$DOCKER_DIR/nginx_ssl.conf"
    generate_conf "$DOCKER_DIR/nginx_reverse_proxy.conf"
fi

if [ ! -f "$DOCKER_DIR/supervisord.conf" ]; then
    echo_title "GENERATE SUPERVISOR CONFIGURATION"
    generate_conf "$DOCKER_DIR/supervisord.conf"
fi

# TODO redis password
