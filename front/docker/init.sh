DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT/scripts/utils.sh"
export INSTALL_MODE="full_install"

FRONT_ENV="$FRONT_ROOT/app/config/.env"
DOCKER_ENV="$DOCKER_DIR/.env"

update_app_env "$FRONT_ENV" || error "Failed to setup $FRONT_ENV."
source "$FRONT_ENV"

setup_env "$DOCKER_ENV" || error "Failed to setup $DOCKER_ENV."
source "$DOCKER_ENV"

setup_cantaloupe "quick_install"

# if app/logs/app_log.log does not exist, create it
if [ ! -f "$FRONT_ROOT/app/logs/app_log.log" ]; then
    get_password && echo || exit
    color_echo yellow "Log file creation"
    touch "$FRONT_ROOT/app/logs/app_log.log"
    touch "$FRONT_ROOT/app/logs/download.log"
    touch "$FRONT_ROOT/app/logs/iiif.log"
    sudo chown -R "$USERID:$USERID" "$FRONT_ROOT"/app/logs
fi

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    get_password && echo || exit
    color_echo yellow "Creation of $DATA_FOLDER"
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER/mediafiles" ]; then
    get_password && echo || exit
    sudo mkdir -p "$DATA_FOLDER"/mediafiles
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

if [ ! -d "$DATA_FOLDER/sas" ]; then
    get_password && echo || exit
    sudo mkdir -p "$DATA_FOLDER/sas"
    sudo chown -R "$USERID":"$USERID" "$DATA_FOLDER/sas"
fi

generate_conf() {
    local conf_file="$1"
    local template_file="${conf_file}.template"

    if [ ! -f "$template_file" ]; then
        color_echo red "Template file '$template_file' not found. Cannot generate $conf_file."
        return 1
    fi

    if [ ! -f "$conf_file" ] || ! check_template_hash "$template_file"; then
        color_echo yellow "Updating $conf_file..."
        cp "$template_file" "$conf_file"

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

        store_template_hash "$template_file"
    fi
}

generate_conf "$DOCKER_DIR/nginx.conf"
generate_conf "$DOCKER_DIR/nginx_external.conf"
generate_conf "$DOCKER_DIR/nginx_ssl.conf"
generate_conf "$DOCKER_DIR/nginx_reverse_proxy.conf"
generate_conf "$DOCKER_DIR/supervisord.conf"
