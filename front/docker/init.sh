#!/bin/env bash

set -e

DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT/scripts/utils.sh"
export INSTALL_MODE="full_install"

FRONT_ENV="$FRONT_ROOT/app/config/.env"
FRONT_ENV_TEMPLATE="$FRONT_ROOT/app/config/.env.template"
DOCKER_ENV="$DOCKER_DIR/.env"
DOCKER_ENV_TEMPLATE="$DOCKER_DIR/.env.template"

# backup DOCKER_ENV, copy the global .env to docker/ folder.
if [ -f "$DOCKER_ENV" ]; then cp "$DOCKER_ENV" "$DOCKER_ENV.backup"; fi;
if [ -f "$FRONT_ENV" ];
then cp "$FRONT_ENV" "$DOCKER_ENV";
else cp "$FRONT_ENV_TEMPLATE" "$DOCKER_ENV";
fi

# $DOCKER_ENV is now a copy of $FRONT_ENV.
# merge it with defaults defined in $DOCKER_ENV_TEMPLATE
prev_line=""
add_env=""
while IFS="" read -r line; do
    if [[ $line =~ ^[^#]*= ]]; then
        param=$(echo "$line" | cut -d'=' -f1)
        val=$(echo "$line" | cut -d'=' -f2)
        desc=$(get_env_desc "$line" "$prev_line")

        # 1. $param is in $DOCKER_ENV => update with value in $DOCKER_ENV_TEMPLATE
        if grep -Eq "^${param}=" "$DOCKER_ENV"; then
            echo "+++ $param"
            sed_repl_inplace "s~^$param=.*$~$param=$val~" "$DOCKER_ENV";
        # 2. $param is not in $DOCKER_ENV_TEMPLATE => append param, default value and description from $DOCKER_ENV_TEMPLATE to $DOCKER_ENV.
        else
            echo "--- $param"
            add_env="$add_env\n# $desc\n$param=$val\n";
        fi
    fi;
    prev_line="$line"
done < "$DOCKER_ENV_TEMPLATE"
echo -e "$add_env" >> "$DOCKER_ENV"

# place derived variables in $DOCKER_ENV at the end of the file
prev_line=""
env_default=""  # user-defined variables
env_ignore=""  # variables derived from others that should not be edited
while IFS="" read -r line; do
    if [[ $line =~ ^[^#]*= ]]; then
        param=$(echo "$line" | cut -d'=' -f1)
        val=$(echo "$line" | cut -d'=' -f2)
        desc=$(get_env_desc "$line" "$prev_line")
        full="# $desc\n$param=$val\n"

        if [[ "$desc" =~ ^\s*IGNORE\s*$ ]]; then
            env_ignore="$env_ignore\n$full"
        else
            env_default="$env_default\n$full"
        fi
    fi
    prev_line="$line"
done < "$DOCKER_ENV"
echo -e "$env_default$env_ignore" > "$DOCKER_ENV"
exit 1

# TODO: move # IGNORE variables at the end of the script.

# prompt user for the rest

update_app_env "$FRONT_ENV" || error "Failed to setup $FRONT_ENV."
source "$FRONT_ENV"

# TODO: make internal port constant and have only external PORTS (i.e only ports defined in docker/.env mutable)
# TODO: make FRONT_ENV ports hard coded when docker is enabled
setup_env "$DOCKER_ENV" || error "Failed to setup $DOCKER_ENV."
source "$DOCKER_ENV"

setup_cantaloupe "quick_install"

# if app/logs/app_log.log does not exist, create it
if [ ! -f "$FRONT_ROOT/app/logs/app_log.log" ]; then
    color_echo yellow "Log file creation (your password is required to set permissions)"
    get_password && echo || exit
    touch "$FRONT_ROOT/app/logs/app_log.log"
    touch "$FRONT_ROOT/app/logs/download.log"
    touch "$FRONT_ROOT/app/logs/iiif.log"
    sudo chown -R "$USERID:$USERID" "$FRONT_ROOT"/app/logs
fi

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    color_echo yellow "Creation of $DATA_FOLDER folder (your password is required to set permissions)"
    get_password && echo || exit
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ ! -d "$DATA_FOLDER/mediafiles" ]; then
    color_echo yellow "Creation of $DATA_FOLDER/mediafiles folder (your password is required to set permissions)"
    get_password && echo || exit
    sudo mkdir -p "$DATA_FOLDER"/mediafiles
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"/mediafiles
fi

# if [ ! -d "$DATA_FOLDER/sas" ]; then
#     color_echo yellow "Creation of $DATA_FOLDER/sas folder (your password is required to set permissions)"
#     get_password && echo || exit
#     sudo mkdir -p "$DATA_FOLDER/sas"
#     sudo chown -R "$USERID":"$USERID" "$DATA_FOLDER/sas"
# fi

if [ ! -d "$DATA_BACKUP" ]; then
    color_echo yellow "Creation of $DATA_BACKUP folder (your password is required to set permissions)"
    get_password && echo || exit
    sudo mkdir -p "$DATA_BACKUP"
    # sudo chown -R "$USERID":"$USERID" "$DATA_FOLDER/sas"
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
        # sed_repl_inplace "s~SAS_PORT~$SAS_PORT~" "$conf_file"
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
