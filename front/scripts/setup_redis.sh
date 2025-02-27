#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

INSTALL_TYPE=$(get_install_type "$1")

echo_title "REDIS DATABASE INITIALIZATION"

redis_psw=$(get_env_value "REDIS_PASSWORD" "$APP_ENV")
redis_conf_file=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
options=("yes" "no")

redis_restart() {
    case "$OS" in
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

# $redis_conf_file defined above only works if no redis password is defined (else, redis-cli fails with NOAUTH)
# => exit if $redis_conf_file is undefined. there's probably a password locking access to redis-cli.
redis_no_conf_file_exit() {
    file=$1
    if [ -z "$file" ]; then
        color_echo red "ERROR: Could not find a Redis config file. The password cannot be changed automatically. This can happen if your Redis has another password defined."
        color_echo red "       You can change the password manually by updating the 'requirepass' in your Redis config file to match 'REDIS_PASSWORD'."
        color_echo red "       Alternatively, you can update the 'REDIS_PASSWORD' to match the one defined in your Redis config file."
        color_echo red "       The 'REDIS_PASSWORD' is defined in '$APP_ENV'"
        exit 1
    fi
}

# TODO: it's possible (maybe) to set password from redis-cli, which seems more stable.
redis_set_password() {
    redis_no_conf_file_exit "$redis_conf_file"
    sudo_sed_repl_inplace "s/^requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf_file"
    sudo_sed_repl_inplace "s/^# *requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf_file"
    sudo_sed_repl_inplace "s/^requirepass$/requirepass $redis_psw/" "$redis_conf_file"
    sudo_sed_repl_inplace "s/^# *requirepass$/requirepass $redis_psw/" "$redis_conf_file"
    redis_restart
}

redis_set_no_password() {
    redis_no_conf_file_exit "$redis_conf_file"
    sed_repl_inplace "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=~" "$APP_ENV"
    sudo_sed_repl_inplace "s/^requirepass [^ ]*/# requirepass $redis_psw/" "$redis_conf_file"
    redis_restart
}

# only runs if a redis password is defined
if [ -n "$redis_psw" ]; then
    if [ "$INSTALL_TYPE" = "quick_install" ]; then
        redis_set_no_password
    else
        color_echo blue "\nYou defined a redis password in $APP_ENV. Do you want to secure redis with it (not necessary on local)?"
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
