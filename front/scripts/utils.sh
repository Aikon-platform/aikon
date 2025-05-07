#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$SCRIPT_DIR")"

FRONT_ENV="$FRONT_ROOT/app/config/.env"

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

# gets a password and validates it by running a dummy cmd.
# parent process must call the function with `get_password || exit` to exit the script if `SUDO_PSW` is invalid
get_password() {
    if [ -z "$SUDO_PSW" ]; then
        read -s -p "Enter your sudo password: " SUDO_PSW
        echo
        echo "$SUDO_PSW" | sudo -S whoami > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "Invalid sudo password. Exiting..."
            return 1
        fi
        return 0
    fi
}

fresh_shell() {
    # reset exported variables
    if [ "$OS" = "Linux" ]; then
        exec bash
    else
        exec zsh
    fi
}

# inline replacement in file $file with sed expression $sed_expr
# `sed -i` can't be used in the same way with Linux and Mac: it's `sed -i` on Linux, `sed -i ""` on Mac.
# we must define the sed variants as functions and can't just store the variants as strings because this
# messes up word splitting and quoting (especially when using `sudo "$sed_command_as_string"`).
# instead, we define a function that takes an expression and a file and runs the replacement.
# see: https://unix.stackexchange.com/a/444949
sed_repl_inplace() {
    sed_expr="$1"
    file="$2"

    if [ "$OS" = "Linux" ]; then
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

    if [ "$OS" = "Linux" ]; then
        [ -n "$SUDO_PSW" ] && echo "$SUDO_PSW" | sudo -S sed -i -e "$sed_expr" "$file" || sudo sed -i -e "$sed_expr" "$file"
    else
        [ -n "$SUDO_PSW" ] && echo "$SUDO_PSW" | sudo -S sed -i "" -e "$sed_expr" "$file" || sudo sed -i "" -e "$sed_expr" "$file"
    fi
}

DEFAULT_PARAMS=()
is_in_default_params() {
    local param=$1
    for default_param in "${DEFAULT_PARAMS[@]}"; do
        if [ "$param" = "$default_param" ]; then
            return 0
        fi
    done
    return 1
}

get_template_hash() {
    local template_file=$1
    md5sum "$template_file" | awk '{print $1}'
}

store_template_hash() {
    local template_file=$1
    local hash_file="${template_file}.hash"
    local current_hash=$(get_template_hash "$template_file")
    echo "$current_hash" > "$hash_file"
}

check_template_hash() {
    local template_file=$1
    local hash_file="${template_file}.hash"

    if [ ! -f "$hash_file" ]; then
        store_template_hash "$template_file"
        return 1  # Hash file didn't exist, template is new
    fi

    local stored_hash=$(cat "$hash_file")
    local current_hash=$(get_template_hash "$template_file")

    if [ "$stored_hash" != "$current_hash" ]; then
        store_template_hash "$template_file"
        return 1  # Hash changed
    fi

    return 0  # Hash unchanged
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

    if [ "$default_val" != "$current_val" ]; then
        prompt="Press enter for $(color_echo 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        prompt="Press enter to keep $(color_echo 'cyan' "$current_val")"
    else
        prompt="Enter value"
    fi

    prompt="$prompt [x for empty value]"
    read -p "$env_var $desc"$'\n'"$prompt: " value </dev/tty

    if [ "$value" = "x" ]; then
        export new_value=""  # if user entered a space character, return empty value
    else
        export new_value="${value:-$default_val}"
    fi
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
    echo "$desc"
}

get_default_val() {
    local param=$1
    if [ -n "${!param}" ]; then
        # if the value is already exported in the current shell, use it as default
        default_val="${!param}"

    elif [[ "$param" =~ ^.*(PASSWORD|SECRET).*$ ]]; then
        default_val="$(generate_random_string)"

    elif [[ "$param" = "MEDIA_DIR" ]]; then
        default_val="$FRONT_ROOT"/app/mediafiles

    elif [[ "$param" = "DOCKER" ]]; then
        if [[ "$(get_env_value "TARGET" "$FRONT_ENV")" = "prod" ]]; then
            default_val="True"
        else
            default_val="False"
        fi

    elif [[ "$param" = "DEBUG" ]]; then
        if [[ "$(get_env_value "DOCKER" "$FRONT_ENV")" = "True" ]]; then
            default_val="False"
        else
            default_val="True"
        fi

    elif [[ "$param" = "REDIS_HOST" ]]; then
        if [[ "$(get_env_value "DOCKER" "$FRONT_ENV")" = "True" ]]; then
            default_val="redis"
        else
            default_val="localhost"
        fi

    elif [ "$param" = "EMAIL_HOST_USER" ]; then
        app_name=$(get_env_value "APP_NAME" "$FRONT_ENV")
        app_name=${app_name:-"app"}
        default_val=$([ -n "$app_name" ] && echo "$app_name@mail.com" || echo "$current_val")

    elif [ "$param" = "CANTALOUPE_BASE_URI" ]; then
        default_val="https://"$(get_env_value "PROD_URL" "$FRONT_ENV")

    elif [ "$param" = "CANTALOUPE_IMG" ]; then
        default_val=$(get_env_value "MEDIA_DIR" "$FRONT_ENV")"/img/"
        # if [ "$OS" = "Linux" ]; then
        #     default_val=$(get_env_value "MEDIA_DIR" "$FRONT_ENV")"/img/"
        # else
        #     default_val=$(get_env_value "MEDIA_DIR" "$FRONT_ENV")"/img"
        # fi

    elif [ "$param" = "CANTALOUPE_PORT" ]; then
        default_val=$(get_env_value "CANTALOUPE_PORT" "$FRONT_ENV")

    elif [ "$param" = "CANTALOUPE_PORT_HTTPS" ]; then
        default_val=$(get_env_value "CANTALOUPE_PORT_HTTPS" "$FRONT_ENV")

    elif [ "$param" = "CANTALOUPE_DIR" ]; then
        default_val="$FRONT_ROOT"/cantaloupe

    else
        default_val=$(get_env_value "$param" "$env_file")
    fi
    echo "$default_val"
}

update_env_var() {
    local value=$1
    local param=$2
    local env_file=$3
    sed_repl_inplace "s~^$param=.*~$param=$value~" "$env_file"
}

export_env() {
    local env_file=$1
    set -a # Turn on allexport mode
    source "$env_file"
    set +a # Turn off allexport mode
}

update_env() {
    local env_file=$1

    local prev_line=""
    while IFS= read -r line; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            desc=$(get_env_desc "$line" "$prev_line")
            default_val=$(get_default_val $param)
            current_val=$(get_env_value "$param" "$env_file")

            if [ "$INSTALL_MODE" = "full_install" ]; then
                # For full install, all variables are prompted
                prompt_user "$param" "$default_val" "$current_val" "$desc"
            elif [ -n "${!param}" ]; then
                # If variable is already set in the current shell, use it as default
                new_value="${!param}"
            elif is_in_default_params "$param"; then
                # If param is in default params, use default value if it exists
                new_value="$default_val"
            else
                prompt_user "$param" "$default_val" "$current_val" "$desc"
            fi

            update_env_var "$new_value" "$param" "$env_file"
        fi
        prev_line="$line"
    done < "$env_file"
}

setup_env() {
    local env_file=$1
    local template_file="${env_file}.template"
    local default_params=("${@:2}")  # All arguments after $1 are default params
    DEFAULT_PARAMS=("${default_params[@]}")

    if [ ! -f "$env_file" ]; then
        color_echo yellow "\nCreating $env_file"
        cp "$template_file" "$env_file"
    elif ! check_template_hash "$template_file"; then
        color_echo yellow "\nUpdating $env_file"
        # the env file has already been created, but the template has changed
        export_env "$env_file" # source current values to copy them in new env
        cp "$env_file" "${env_file}.backup"
        cp "$template_file" "$env_file"
    else
        # options=("yes" "no")
        #
        # color_echo yellow "\n$env_file is up-to-date. Do you want to regenerate it again?"
        # answer=$(printf "%s\n" "${options[@]}" | fzy)
        # if [ "$answer" = "yes" ]; then
        #     rm "${template_file}.hash"
        #     setup_env $env_file
        #     return 0
        # fi
        color_echo cyan "\nSkipping..."
        export_env "$env_file"
        return 0
    fi

    if [ -z "$INSTALL_MODE" ]; then
        select_install_mode
    fi

    update_env "$env_file"
    export_env "$env_file"
}

update_app_env() {
    env_file=${1:-$FRONT_ENV}
    default_params=("DEBUG" "C_FORCE_ROOT" "MEDIA_DIR" "CONTACT_MAIL" "POSTGRES_DB" "POSTGRES_USER"
        "DB_PORT" "API_PORT" "ALLOWED_HOSTS" "SAS_USERNAME" "SAS_PORT" "SAS_PASSWORD" "SECRET_KEY" "FRONT_PORT"
        "PROD_API_URL" "CANTALOUPE_PORT" "CANTALOUPE_PORT_HTTPS" "REDIS_HOST" "REDIS_PORT" "REDIS_PASSWORD"
        "EMAIL_HOST" "EMAIL_HOST_USER" "EMAIL_HOST_PASSWORD" "DEFAULT_FROM_EMAIL" "APP_LOGO" "HTTP_PROXY" "HTTPS_PROXY")

    setup_env "$env_file" "${default_params[@]}"

    media_dir=$(get_env_value "MEDIA_DIR" "$env_file")
    default_media_dir="$FRONT_ROOT"/app/mediafiles

    is_docker=$(get_env_value "DOCKER" "$env_file")
    if [ "$media_dir" != "$default_media_dir" ] && [ "$is_docker" != "True" ]; then
        # when choosing a nonstandard media directory, copy the structure from the default media directory
        cp -r "$default_media_dir" "$media_dir"
    fi
}

setup_cantaloupe() {
    export INSTALL_MODE=${1:-$INSTALL_MODE}
    cantaloupe_dir=${2:-$FRONT_ROOT/cantaloupe}
    local default_params=("CANTALOUPE_BASE_URI" "CANTALOUPE_IMG" "CANTALOUPE_PORT" "CANTALOUPE_PORT_HTTPS" "CANTALOUPE_DIR")
    setup_env "$cantaloupe_dir"/.env "${default_params[@]}" || return 1

    config_cantaloupe="$cantaloupe_dir"/cantaloupe.properties

    chmod +x "$cantaloupe_dir"/start.sh
    source "$cantaloupe_dir"/.env

    if [ ! -f "$config_cantaloupe" ] || ! check_template_hash "$config_cantaloupe.template"; then
         cp "$config_cantaloupe.template" "$config_cantaloupe"

         sed_repl_inplace "s~CANTALOUPE_BASE_URI~$CANTALOUPE_BASE_URI~" "$config_cantaloupe"
         sed_repl_inplace "s~CANTALOUPE_IMG~$CANTALOUPE_IMG~" "$config_cantaloupe"
         sed_repl_inplace "s~CANTALOUPE_PORT~$CANTALOUPE_PORT~" "$config_cantaloupe"
         sed_repl_inplace "s~CANTALOUPE_PORT_HTTPS~$CANTALOUPE_PORT_HTTPS~" "$config_cantaloupe"
         sed_repl_inplace "s~CANTALOUPE_DIR~$CANTALOUPE_DIR~" "$config_cantaloupe"
         store_template_hash "$config_cantaloupe.template"
    else
         color_echo green "$config_cantaloupe is up-to-date."
    fi
}

get_child_pids() {
    local all_pids=()

    for pid in $(pgrep -P "$1" 2>/dev/null); do
        all_pids+=("$pid")
        local grandchild_pids=$(get_child_pids "$pid")
        for gchild in $grandchild_pids; do
            all_pids+=("$gchild")
        done
    done

    echo "${all_pids[@]}"
}

cleanup_pids() {
    local parent_pids=($1)
    local services="$2"
    local psw="$3"

    local use_sudo=0
    if [ -n "$psw" ]; then
        use_sudo=1
    fi

    color_echo blue "Shutting down processes..."
    local all_pids=()
    for pid in "${parent_pids[@]}"; do
        all_pids+=("$pid")
        for child in $(get_child_pids "$pid"); do
            all_pids+=("$child")
        done
    done
    # remove duplicates
    all_pids=($(echo "${all_pids[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    for pid in "${all_pids[@]}"; do
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done

    sleep 2

    for pid in "${all_pids[@]}"; do
        if ps -p "$pid" > /dev/null 2>&1; then
            if [ "$use_sudo" -eq 1 ]; then
                echo "$psw" | sudo -S kill -9 "$pid" 2>/dev/null
            else
                kill -9 "$pid" 2>/dev/null
            fi
        fi
    done

    local pid_still_running=0
    for pid in "${all_pids[@]}"; do
        if ps -p "$pid" > /dev/null 2>&1; then
            pid_still_running=1
            color_echo red "⚠️ Process $pid is still running!"
        fi
    done

    if [ -n "$services" ]; then
        local remaining=$(ps aux | grep -E "$services" | grep -v grep | wc -l)
        if [ "$remaining" -gt 0 ]; then
            color_echo red "⚠️ $remaining processes might still be running. You may need to manually kill them."
            ps aux | grep -E "$services" | grep -v grep
        elif [ "$pid_still_running" -eq 0 ]; then
            color_echo blue "All processes successfully terminated."
        fi
    else
        if [ "$pid_still_running" -eq 0 ]; then
            color_echo blue "All tracked processes successfully terminated."
        fi
    fi

    return 0
}

ask() {
    options=("yes" "no")
    color_echo blue "$1"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    if [ "$answer" = "no" ]; then
        exit 1
    fi
}

error() {
    color_echo red "$1"
    exit 1
}

run_script() {
    local script_name="$1"
    local description="$2"
    local script_dir=${3:-${SCRIPT_DIR}}
    options=("yes" "no")

    color_echo blue "Do you want to run $description?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    if [ "$answer" = "yes" ]; then
        bash "$script_dir/$script_name" \
        && color_echo green "$description completed successfully" \
        || color_echo red "$description failed with exit code. Continuing..."
    else
        color_echo cyan "Skipping $description"
    fi
    echo ""
}
