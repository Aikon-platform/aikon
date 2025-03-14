DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

# TODO add more echo and interactivity to let the user know what is happening

source "$FRONT_ROOT"/scripts/functions.sh

# if docker/.env does not exist, create it
if [ ! -f "$FRONT_ROOT/docker/.env" ]; then
    echo_title "DOCKER ENVIRONMENT VARIABLES"
    cp "$FRONT_ROOT/docker/.env.template" "$FRONT_ROOT"/docker/.env
    update_env "$FRONT_ROOT"/docker/.env
fi

# if ../app/config/.env does not exist, create it
if [ ! -f "$FRONT_ROOT"/app/config/.env ]; then
    echo_title "DJANGO APP ENVIRONMENT VARIABLES"
    # TODO copy environment variables from docker env
    cp "$FRONT_ROOT"/app/config/.env.template "$FRONT_ROOT"/app/config/.env
    update_env "$FRONT_ROOT"/app/config/.env
fi

# if ../cantaloupe/.env does not exist, create it
CANTALOUPE_DIR="$FRONT_ROOT"/cantaloupe
if [ ! -f "$CANTALOUPE_DIR/.env" ]; then
    echo_title "CANTALOUPE SETUP"
    cp "$CANTALOUPE_DIR/.env.template" "$CANTALOUPE_DIR/.env"
    update_cantaloupe_env "quick_install"
    update_cantaloupe_properties "$CANTALOUPE_DIR"
fi

# if app/logs/app_log.log does not exist, create it
if [ ! -f "$FRONT_ROOT"/app/logs/app_log.log ]; then
    touch "$FRONT_ROOT"/app/logs/app_log.log
    touch "$FRONT_ROOT"/app/logs/download.log
    touch "$FRONT_ROOT"/app/logs/iiif.log
    chown -R "$USERID:$USERID" "$FRONT_ROOT"/app/logs
fi

source "$FRONT_ROOT"/app/config/.env
source "$FRONT_ROOT"/docker/.env

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER"/mediafiles ]; then
    cp -r "$FRONT_ROOT"/app/mediafiles "$DATA_FOLDER"/
    chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

if [ ! -d "$DATA_FOLDER"/sas ]; then
    mkdir -p "$DATA_FOLDER"/sas
    chown -R "$USERID":"$USERID" "$DATA_FOLDER"/sas
fi

# if nginx_conf does not exist, create it
if [ ! -f "$FRONT_ROOT"/docker/nginx_conf ]; then
    cp "$FRONT_ROOT"/docker/nginx.conf.template "$FRONT_ROOT"/docker/nginx_conf

    sed_repl_inplace "s~DJANGO_PORT~$DJANGO_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~NGINX_PORT~$NGINX_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~SAS_PORT~$SAS_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~PROD_URL~$PROD_URL~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~SSL_CERTIFICATE~$SSL_CERTIFICATE~" "$FRONT_ROOT"/docker/nginx_conf
    sed_repl_inplace "s~SSL_KEY~$SSL_KEY~" "$FRONT_ROOT"/docker/nginx_conf
fi

# TODO redis password
