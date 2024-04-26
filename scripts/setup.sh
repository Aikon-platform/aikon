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

OS=$(get_os)

install_packages() {
    case $OS in
        Linux)
            wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
            sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
            sudo apt update
            sudo apt-get install wget ca-certificates
            sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
            ;;
        Mac)
            brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript
            brew services start postgresql
            brew services start redis
            ;;
        *)
            colorEcho red "Unsupported OS: $os"
            exit 1
            ;;
    esac
}

colorEcho blue "\nInstalling prompt utility fzy..."
case $OS in
    Linux)
        sudo apt install fzy
        ;;
    Mac)
        brew install fzy
        ;;
    *)
        colorEcho red "Unsupported OS: $os"
        exit 1
        ;;
esac

options=("yes" "no")
colorEcho blue "\nInstall system packages?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

case $answer in
    "yes")
        echoTitle "SYSTEM PACKAGES INSTALL"
        install_packages
        ;;
    *)
        ;;
esac

colorEcho blue "\nInstall python virtual environment?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

case $answer in
    "yes")
        echoTitle "VIRTUAL ENVIRONMENT SET UP"
        python3.10 -m venv venv
        source venv/bin/activate
        pip install -r app/requirements-dev.txt
        pre-commit install
        ;;
    *)
        ;;
esac

colorEcho blue "\nGenerate app/config/.env file?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

APP_ENV="$APP_ROOT"/app/config/.env
case $answer in
    "yes")
        echoTitle "APP ENV GENERATION"
        cp "$APP_ENV".template "$APP_ENV"
        update_env "$APP_ENV"
        ;;
    *)
        ;;
esac

update_cantaloupe_env() {
    ordered_params=("BASE_URI" "FILE_SYSTEM_SOURCE" "HTTP_PORT" "HTTPS_PORT" "LOG_PATH")
    for param in "${ordered_params[@]}"; do
        current_val=$(get_env_value "$param" "$CANTALOUPE_ENV_FILE")
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
        sed -i "" -e "s~^$param=.*~$param=$new_value~" "$CANTALOUPE_ENV_FILE"
    done
}

colorEcho blue "\nGenerate cantaloupe/.env file?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

case $answer in
    "yes")
        echoTitle "CANTALOUPE ENV GENERATION"
        CANTALOUPE_ENV_FILE="$APP_ROOT"/cantaloupe/.env
        cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"
        update_cantaloupe_env
        bash "$APP_ROOT"/cantaloupe/init.sh
        ;;
    *)
        ;;
esac

db_name=$(get_env_value "DB_NAME" "$APP_ENV")
db_user=$(get_env_value "DB_USERNAME" "$APP_ENV")
colorEcho blue "\nCreate a new database named $db_name?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

case $answer in
    "yes")
        echoTitle "DATABASE GENERATION"
        colorEcho yellow "\n⚠️The script will create a app user named $db_user: at the end, you will be prompted twice to enter a password for this user"
        ok=("ok")
        printf "%s\n" "${ok[@]}" | fzy
        bash "$SCRIPT_DIR"/new_db.sh "$db_name"
        ;;
    *)
        ;;
esac


redis_psw=$(get_env_value "REDIS_PASSWORD" "$APP_ENV")
if [ -n "$redis_psw" ]; then
    colorEcho blue "\nYou defined a redis password in $APP_ENV. Do you want to secure redis with it (not necessary on local)?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    case $answer in
        "yes")
            echoTitle "PASSWORD SETTING FOR REDIS"
            redis_conf=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
            sudo sed -i "" -e "s/^requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
            sudo sed -i "" -e "s/# requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
            case $os in
                "Linux")
                    sudo systemctl restart redis-server
                    ;;
                "Mac")
                    brew services restart redis
                    ;;
                *)
                    ;;
                esac
            ;;
        "no")
            sed -i "" -e "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=~" "$APP_ENV"
            sudo sed -i "" -e "s/^requirepass [^ ]*/# requirepass $redis_psw/" "$redis_conf"
            ;;
        *)
            ;;
    esac
fi

: <<'END'
sas_psw=$(get_env_value "SAS_PASSWORD" "$APP_ENV")
sas_user=$(get_env_value "SAS_USERNAME" "$APP_ENV")
if [ -n "$sas_psw" ]; then
    colorEcho blue "\nYou defined a password for SAS in $APP_ENV. Do you want to secure SAS with it (not necessary on local)?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    case $answer in
        "yes")
            echoTitle "PASSWORD SETTING FOR SAS"
            nginx_dir=$(dirname "$(nginx -V 2>&1 | grep -oE -- '--conf-path=[^ ]+' | cut -d= -f2)")
            sudo sh -c "echo -n '$sas_user:' >> $nginx_dir/.htpasswd"
            sudo sh -c "openssl passwd $sas_psw >>$nginx_dir/.htpasswd"
            case $os in
                "Linux")
                    sudo systemctl restart nginx
                    ;;
                "Mac")
                    brew services restart nginx
                    ;;
                *)
                    ;;
                esac
            ;;
        "no")
            sed -i "" -e "s~^SAS_PASSWORD=.*~SAS_PASSWORD=~" "$APP_ENV"
            ;;
        *)
            ;;
    esac
fi
END

echoTitle "🎉 ALL SET UP! 🎉"
colorEcho blue "\nYou can now run the server with: "
colorEcho cyan "              bash run.sh"
