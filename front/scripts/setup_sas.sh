SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

os=$(get_os)
sas_psw=$(get_env_value "SAS_PASSWORD" "$APP_ENV")
sas_user=$(get_env_value "SAS_USERNAME" "$APP_ENV")

if [ -n "$sas_psw" ]; then
    colorEcho blue "\nYou defined a password for SAS in $APP_ENV. Do you want to secure SAS with it (not necessary on local)?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    case $answer in
        "yes")
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
