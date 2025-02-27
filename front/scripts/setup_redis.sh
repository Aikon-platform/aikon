#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

INSTALL_TYPE=$(get_install_type "$1")

echoTitle "REDIS DATABASE INITIALIZATION"

redis_psw=$(get_env_value "REDIS_PASSWORD" "$APP_ENV")
options=("yes" "no")

redis_set_password() {
    redis_conf=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
    sudo_sed_repl_inplace "s/^requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
    sudo_sed_repl_inplace "s/# requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
    case $OS in
        "Linux")
            sudo systemctl restart redis-server
            ;;
        "Mac")
            brew services restart redis
            ;;
        *)
            ;;
    esac
}

redis_set_no_password() {
    redis_conf=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
    sed_repl_inplace "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=~" "$APP_ENV"
    sudo_sed_repl_inplace "s/^requirepass [^ ]*/# requirepass $redis_psw/" "$redis_conf"
}

# only runs if a redis password is defined
if [ -n "$redis_psw" ]; then
    if [ "$INSTALL_TYPE" = "quick_install" ]; then
        redis_set_no_password
    else
        colorEcho blue "\nYou defined a redis password in $APP_ENV. Do you want to secure redis with it (not necessary on local)?"
        answer=$(printf "%s\n" "${options[@]}" | fzy)
        case $answer in
            "yes")
                redis_set_password
                ;;
            "no")
                redis_set_no_password
                ;;
        esac

    fi
fi
