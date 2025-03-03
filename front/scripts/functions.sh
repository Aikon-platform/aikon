#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

color_echo() {
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

echo_title(){
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

    color_echo purple "\n\n$sep_line\n$title\n$sep_line"
}

# the sed at the end removes trailing non-alphanumeric chars.
generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n' | sed -r -e "s/[^a-zA-Z0-9]+$//")"
}

prompt_user() {
    env_var=$(color_echo 'red' "$1")
    default_val="$2"
    current_val="$3"
    desc="$4"

    if [ "$2" != "$3" ]; then
        default="Press enter for $(color_echo 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        default="Press enter to keep $(color_echo 'cyan' "$current_val")"
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

get_env_desc() {
    current_line="$1"
    prev_line="$2"
    desc=""
    if [[ $prev_line =~ ^# ]]; then
        desc=$(echo "$prev_line" | sed 's/^#\s*//')
    fi
    echo "$prev_line"
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

export OS
OS=$(get_os)

# returns "quick_install"|"full_install", defaults to "full_install"
get_install_type() {
    [ "$1" = "quick_install" ] && echo "$1" || echo "full_install"
}

# inline replacement in file $file with sed expression $sed_expr
# `sed -i` can't be used in the same way with Linux and Max: it's `sed -i` on Linux, `sed -i ""` on Mac.
# we must define the sed variants as functions and can't just store the variants as strings because this
# messes up word splitting and quoting (especially when using `sudo "$sed_command_as_string"`).
# instead, we define a function that takes an expression and a file and runs the replacement.
# see: https://unix.stackexchange.com/a/444949
sed_repl_inplace() {
    sed_expr="$1"
    file="$2"

    if [ "$(get_os)" = "Linux" ]; then
        sed -i -e "$sed_expr" "$file"
    else
        sed -i "" -e "$sed_expr" "$file"
    fi
}

# sudo does not inherit from bash functions so this is a copy of
# "bash_repl_inplace" with sudo privileges (see: https://stackoverflow.com/a/9448969)
sudo_sed_repl_inplace() {
    sed_expr="$1"
    file="$2"

    if [ "$(get_os)" = "Linux" ]; then
        sudo sed -i -e "$sed_expr" "$file"
    else
        sudo sed -i "" -e "$sed_expr" "$file"
    fi
}

# TODO delete update_env to keep only update_app_env (currently update_env) is only used in front/docker/init.sh
update_env() {
    env_file=$1

    IFS=$'\n' read -d '' -r -a lines < "$env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$env_file")
            desc=$(get_env_desc "$line" "$prev_line")

            # # Extract description from previous line if it exists
            # desc=""
            # if [[ $prev_line =~ ^# ]]; then
            #     desc=$(echo "$prev_line" | sed 's/^#\s*//')
            # fi

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
            sed_repl_inplace "s~^$param=.*~$param=$new_value~" "$env_file"
        fi
        prev_line="$line"
    done
}

update_app_env() {
    env_file=$1
    front_dir=$2
    install_type=$(get_install_type "$3")

    default_params=("APP_NAME" "APP_LANG" "DEBUG" "C_FORCE_ROOT" "MEDIA_DIR" "CONTACT_MAIL" "POSTGRES_DB" "POSTGRES_USER" "DB_HOST" "DB_PORT" "ALLOWED_HOSTS" "SAS_USERNAME" "SAS_PORT" "CANTALOUPE_PORT" "CANTALOUPE_PORT_HTTPS" "REDIS_HOST" "REDIS_PORT" "REDIS_PASSWORD" "EMAIL_HOST" "EMAIL_HOST_USER" "APP_LOGO")

    IFS=$'\n' read -d '' -r -a lines < "$env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then

            # extract param and current value from .env
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$env_file")
            desc=$(get_env_desc "$line" "$prev_line")

            # # Extract description from previous line if it exists
            # desc=""
            # if [[ $prev_line =~ ^# ]]; then
            #     desc=$(echo "$prev_line" | sed 's/^#\s*//')
            # fi

            # get a default value
            if [ "$param" = "MEDIA_DIR" ]; then
                default_val="$front_dir"/app/mediafiles
            elif [[ "$param" =~ ^.*(PASSWORD|SECRET).*$ ]]; then
                default_val="$(generate_random_string)"
            elif [ "$param" = "EMAIL_HOST_USER" ]; then
                app_name=$(get_env_value "APP_NAME" "$env_file")
                default_val=$([ -n "$app_name" ] && echo "$app_name@gmail.com" || echo "$current_val")
            else
                default_val="$current_val"
            fi

            # update the .env file, without prompting user if quick_install and the parameter name is part of $default_params
            if [ "$install_type" = "quick_install" ] && [[ " ${default_params[*]} " =~ "$param" ]]; then
                new_value="$default_val"
            else
                new_value=$(prompt_user "$param" "$default_val" "$current_val" "$desc")
                # default media dir aldready has a structure clearly defined in the git repo.
                # when chosing a nonstandard media directory, this structure is not copied,
                # which may cause FileNotFound errors later on.
                if [ "$param" = "MEDIA_DIR" ] && [ "$new_value" != "$default_val" ]; then
                    cp -r "$default_val" "$new_value"
                fi
            fi
            sed_repl_inplace "s~^$param=.*~$param=$new_value~" "$env_file"
        fi
        prev_line="$line"
    done
}

update_cantaloupe_env() {

    install_type=$(get_install_type "$1")

    cantaloupe_env_file="$APP_ROOT"/cantaloupe/.env
    app_env_file="$APP_ROOT"/app/config/.env
    ordered_params=("FILE_SYSTEM_SOURCE" "HTTP_PORT" "HTTPS_PORT" "LOG_PATH")

    IFS=$'\n' read -d '' -r -a lines < "$cantaloupe_env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then

            # extract param and current value from .env
            param=$(echo "$line" | cut -d'=' -f1)
            desc=$(get_env_desc "$line" "$prev_line")
            current_val=$(get_env_value "$param" "$cantaloupe_env_file")
            current_val=$(get_env_value "$param" "$cantaloupe_env_file")

            case $param in
                "BASE_URI")
                    default_val="https://"$(get_env_value "PROD_URL" "$app_env_file")
                    ;;
                "FILE_SYSTEM_SOURCE")
                    default_val=$(get_env_value "MEDIA_DIR" "$app_env_file")"/img"
                    ;;
                "HTTP_PORT")
                    default_val=$(get_env_value "CANTALOUPE_PORT" "$app_env_file")
                    ;;
                "HTTPS_PORT")
                    default_val=$(get_env_value "CANTALOUPE_PORT_HTTPS" "$app_env_file")
                    ;;
                "LOG_PATH")
                    default_val="$APP_ROOT"/cantaloupe
                    ;;
                *)
                    default_val="$current_val"
                    ;;
            esac

            if [ "$install_type" = "quick_install" ] && [[ " ${default_params[*]} " =~ "$param" ]]; then
                new_value="$default_val"
            else
                new_value=$(prompt_user "$param" "$default_val" "$current_val" "$desc")
            fi
            sed_repl_inplace "s~^$param=.*~$param=$new_value~" "$cantaloupe_env_file"
        fi
        prev_line="$line"
    done
}
