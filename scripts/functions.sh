#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

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

echoTitle(){
    sep_line="========================================"
    len_title=${#1}

    if [ "$len_title" -gt 40 ]; then
        sep_line=$(printf "%0.s=" $(seq 1 $len_title))
        title="$1"
    else
        diff=$((38 - len_title))
        half_diff=$((diff / 2))
        sep=$(printf "%0.s=" $(seq 1 $half_diff))

        if [ $((diff % 2)) -ne 0 ]; then
            title="$sep $1 $sep="
        else
            title="$sep $1 $sep"
        fi
    fi

    colorEcho purple "\n\n$sep_line\n$title\n$sep_line"
}

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

prompt_user() {
    env_var=$(colorEcho 'red' "$1")
    default_val="$2"
    current_val="$3"
    desc="$4"

    if [ "$2" != "$3" ]; then
        default="Press enter for $(colorEcho 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        default="Press enter to keep $(colorEcho 'cyan' "$current_val")"
        default_val=$current_val
    fi

    read -p "$env_var $desc"$'\n'"$default: " value
    echo "${value:-$default_val}"
}

get_env_value() {
    param=$1
    env_file=$2
    value=$(awk -F= -v param="$param" '/^[^#]/ && $1 == param {gsub(/"/, "", $2); print $2}' "$env_file")
    echo "$value"
}

get_os() {
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     os=Linux;;
        Darwin*)    os=Mac;;
        CYGWIN*)    os=Cygwin;;
        MINGW*)     os=MinGw;;
        MSYS_NT*)   os=Git;;
        *)          os="UNKNOWN:${unameOut}"
    esac
    echo "${os}"
}

update_env() {
    env_file=$1
    IFS=$'\n' read -d '' -r -a lines < "$env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$env_file")

            # Extract description from previous line if it exists
            desc=""
            if [[ $prev_line =~ ^# ]]; then
                desc=$(echo "$prev_line" | sed 's/^#\s*//')
            fi

            case $param in
                *PASSWORD*)
                    default_val="$(generate_random_string)"
                    ;;
                *SECRET*)
                    default_val="$(generate_random_string)"
                    ;;
                *)
                    default_val="$current_val"
                    ;;
            esac

            new_value=$(prompt_user "$param" "$default_val" "$current_val" "$desc")
            sed -i "" -e "s~^$param=.*~$param=$new_value~" "$env_file"
        fi
        prev_line="$line"
    done
}

update_cantaloupe_env() {
    cantaloupe_env="$APP_ROOT"/cantaloupe/.env
    ordered_params=("BASE_URI" "FILE_SYSTEM_SOURCE" "HTTP_PORT" "HTTPS_PORT" "LOG_PATH")
    for param in "${ordered_params[@]}"; do
        current_val=$(get_env_value "$param" "$cantaloupe_env")
        case $param in
            "BASE_URI")
                default_val="https://"$(get_env_value "PROD_URL" "$APP_ENV")
                ;;
            "FILE_SYSTEM_SOURCE")
                default_val=$(get_env_value "MEDIA_DIR" "$APP_ENV")"/img/"
                ;;
            "HTTP_PORT")
                default_val=$(get_env_value "CANTALOUPE_PORT" "$APP_ENV")
                ;;
            "HTTPS_PORT")
                default_val=$(get_env_value "CANTALOUPE_PORT_HTTPS" "$APP_ENV")
                ;;
            "LOG_PATH")
                default_val="$APP_ROOT"/cantaloupe/
                ;;
            *)
                default_val="$current_val"
                ;;
        esac

        new_value=$(prompt_user "$param" "$default_val" "$current_val")
        sed -i "" -e "s~^$param=.*~$param=$new_value~" "$cantaloupe_env"
    done
}
