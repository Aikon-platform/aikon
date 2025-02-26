#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/functions.sh

OS=$(get_os)

install_packages() {
    if [ "$OS" = "Linux" ]; then
        wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
        sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
        sudo apt update
        sudo apt-get install wget ca-certificates
        sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
    elif [ "$OS" = "Mac" ]; then
        brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript
        brew services start postgresql
        brew services start redis
    else
        colorEcho red "Unsupported OS: $OS"
        exit 1
    fi
}

colorEcho blue "\nInstalling prompt utility fzy..."
if [ "$OS" = "Linux" ]; then
    sudo apt install fzy
elif [ "$OS" = "Mac" ]; then
    brew install fzy
else
    colorEcho red "Unsupported OS: $OS"
    exit 1
fi

options=("yes" "no")

colorEcho blue "\nInstallation for development?"
answer=$(printf "%s\n" "${options[@]}" | fzy)
TARGET="dev"
if [ "$answer" = "no" ]; then
    TARGET="prod"
fi


colorEcho blue "\nInstall system packages?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

if [ "$answer" = "yes" ]; then
    echoTitle "SYSTEM PACKAGES INSTALL"
    install_packages
fi

colorEcho blue "\nInstall python virtual environment?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

if [ "$answer" = "yes" ]; then
    echoTitle "VIRTUAL ENVIRONMENT SET UP"
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install wheel>=0.45.1
    pip install -r app/requirements-$TARGET.txt
    pre-commit install
fi

colorEcho blue "\nGenerate app/config/.env file?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

APP_ENV="$APP_ROOT"/app/config/.env
if [ "$answer" = "yes" ]; then
    echoTitle "APP ENV GENERATION"
    cp "$APP_ENV".template "$APP_ENV"
    update_env "$APP_ENV"
fi

colorEcho blue "\nGenerate cantaloupe/.env file?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

if [ "$answer" = "yes" ]; then
    echoTitle "CANTALOUPE ENV GENERATION"
    CANTALOUPE_ENV_FILE="$APP_ROOT"/cantaloupe/.env
    cp "$CANTALOUPE_ENV_FILE".template "$CANTALOUPE_ENV_FILE"
    update_cantaloupe_env
    bash "$APP_ROOT"/cantaloupe/init.sh
fi

db_name=$(get_env_value "POSTGRES_DB" "$APP_ENV")
db_user=$(get_env_value "POSTGRES_USER" "$APP_ENV")
colorEcho blue "\nCreate a new database named $db_name?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

if [ "$answer" = "yes" ]; then
    echoTitle "DATABASE GENERATION"
    colorEcho yellow "\n⚠️ The script will create a app user named $db_user: at the end, you will be prompted twice to enter a password for this user"
    ok=("ok")
    printf "%s\n" "${ok[@]}" | fzy
    bash "$SCRIPT_DIR"/new_db.sh "$db_name"
fi

# TODO check setup for svelte
colorEcho blue "\nSet up svelte with webpack?"
answer=$(printf "%s\n" "${options[@]}" | fzy)

if [ "$answer" = "yes" ]; then
    if ! command -v npm &> /dev/null; then
        echoTitle "INSTALL NVM & NODE"
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
        nvm install node
        npm install -g webpack webpack-cli
    fi
    echoTitle "SVELTE SETUP"
    cd "$APP_ROOT"/app/webpack
    npm init
    colorEcho blue "\nCompile svelte components using: "
    colorEcho cyan "              npm run build"
fi

redis_psw=$(get_env_value "REDIS_PASSWORD" "$APP_ENV")
if [ -n "$redis_psw" ]; then
    colorEcho blue "\nYou defined a redis password in $APP_ENV. Do you want to secure redis with it (not necessary on local)?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    if [ "$answer" = "yes" ]; then
        echoTitle "PASSWORD SETTING FOR REDIS"
        redis_conf=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
        sudo sed -i "" -e "s/^requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
        sudo sed -i "" -e "s/# requirepass [^ ]*/requirepass $redis_psw/" "$redis_conf"
        if [ "$OS" = "Linux" ]; then
            sudo systemctl restart redis-server
        elif [ "$OS" = "Mac" ]; then
            brew services restart redis
        fi
    else
        sed -i "" -e "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=~" "$APP_ENV"
        sudo sed -i "" -e "s/^requirepass [^ ]*/# requirepass $redis_psw/" "$redis_conf"
    fi
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
            case $OS in
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

echoTitle "🎉 FRONT SET UP COMPLETED ! 🎉"
colorEcho blue "\nYou can now run the server with: "
colorEcho cyan "              bash run.sh"
