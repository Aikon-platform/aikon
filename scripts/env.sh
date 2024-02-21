#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

cp "$APP_ROOT"/app/config/.env.template "$APP_ROOT"/app/config/.env

ENV_FILE="$APP_ROOT"/app/config/.env
MEDIA_DIR="$APP_ROOT/app/mediafiles"

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

colorEcho() {
    Color_Off="\033[0m"
    Red="\033[1;91m"        # Red
    Green="\033[1;92m"      # Green
    Yellow="\033[1;93m"     # Yellow
    Blue="\033[1;94m"       # Blue
    Purple="\033[1;95m"     # Purple
    Cyan="\033[1;96m"       # Cyan

    case "$1" in
        "green") echo -e "$Green$2$Color_Off";;
        "red") echo -e "$Red$2$Color_Off";;
        "blue") echo -e "$Blue$2$Color_Off";;
        "yellow") echo -e "$Yellow$2$Color_Off";;
        "purple") echo -e "$Purple$2$Color_Off";;
        "cyan") echo -e "$Cyan$2$Color_Off";;
        *) echo "$2";;
    esac
}

prompt_user() {
    env_var=$(colorEcho 'red' "$1")
    default_val="$2"
    if [ "$2" = "$3" ]; then
        default="Enter value"
    else
        default="Press enter for $(colorEcho 'cyan' "$2")"
    fi

    read -p "$env_var ($3)"$'\n'"$default: " value
    echo "${value:-$default_val}"
}

get_env_value() {
    param=$1
    value=$(grep -oP "(?<=^$param=\")[^\"]*" "$ENV_FILE")
    echo "$value"
}

update_env() {
    ordered_params=("APP_NAME" "CONTACT_MAIL" "DB_NAME" "DB_USERNAME" "DB_PASSWORD" "ALLOWED_HOSTS" "SECRET_KEY" "MEDIA_DIR" "DEBUG" "DB_HOST" "DB_PORT" "SAS_USERNAME" "SAS_PASSWORD" "SAS_PORT" "CANTALOUPE_PORT" "CANTALOUPE_PORT_HTTPS" "PROD_URL" "GEONAMES_USER" "APP_LANG" "EXAPI_URL" "EXAPI_KEY" "REDIS_PASSWORD")
    for param in "${ordered_params[@]}"; do
        current_val=$(grep -oP "(?<=^$param=\")[^\"]*" "$ENV_FILE")
        case $param in
            "DB_NAME")
                default_val=$(get_env_value "APP_NAME")
                ;;
            "DB_PASSWORD")
                default_val="$(generate_random_string)"
                ;;
            "DB_HOST")
                default_val="localhost"
                ;;
            "DB_PORT")
                default_val="5432"
                ;;
            "SAS_USERNAME")
                default_val=$(get_env_value "DB_USERNAME")
                ;;
            "SAS_PASSWORD")
                default_val="$(generate_random_string)"
                ;;
            "REDIS_PASSWORD")
                default_val=$(generate_random_string)
                ;;
            "SECRET_KEY")
                default_val="$(generate_random_string)"
                ;;
            "ALLOWED_HOSTS")
                default_val="localhost,127.0.0.1,145.238.203.8"
                ;;
            "SAS_PORT")
                default_val="8888"
                ;;
            "CANTALOUPE_PORT")
                default_val="8182"
                ;;
            "CANTALOUPE_PORT_HTTPS")
                default_val="8183"
                ;;
            "MEDIA_DIR")
                default_val=$MEDIA_DIR
                ;;
            *)
                default_val="$current_val"
                ;;
        esac

        new_value=$(prompt_user "$param" "$default_val" "$current_val")
        # sed -i "s~^$param=.*~$param=\"$new_value\"~" "$ENV_FILE"
        sed -i '' -e "s~^$param=.*~$param=\"$new_value\"~" "$ENV_FILE"
    done
}

update_env

CANTALOUPE_ENV_FILE="$APP_ROOT"/cantaloupe/.env
cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"
update_cantaloupe_env() {
    ordered_params=("BASE_URI" "FILE_SYSTEM_SOURCE" "HTTP_PORT" "HTTPS_PORT" "LOG_PATH")
    for param in "${ordered_params[@]}"; do
        current_val=$(grep -oP "(?<=^$param=\")[^\"]*" "$CANTALOUPE_ENV_FILE")
        case $param in
            "BASE_URI")
                default_val="https://"$(get_env_value "PROD_URL")
                ;;
            "FILE_SYSTEM_SOURCE")
                default_val=$(get_env_value "MEDIA_DIR")"/img/"
                ;;
            "HTTP_PORT")
                default_val=$(get_env_value "CANTALOUPE_PORT")
                ;;
            "HTTPS_PORT")
                default_val=$(get_env_value "CANTALOUPE_PORT_HTTPS")
                ;;
            "LOG_PATH")
                default_val="$APP_ROOT"/cantaloupe
                ;;
            *)
                default_val="$current_val"
                ;;
        esac

        new_value=$(prompt_user "$param" "$default_val" "$current_val")
        # sed -i "s~^$param=.*~$param=\"$new_value\"~" "$CANTALOUPE_ENV_FILE"
        sed -i '' -e "s~^$param=.*~$param=\"$new_value\"~" "$CANTALOUPE_ENV_FILE"
    done
}

update_cantaloupe_env
