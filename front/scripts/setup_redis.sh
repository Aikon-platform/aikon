SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

echoTitle "REDIS DATABASE INITIALIZATION"

os=$(get_os)
redis_psw=$(get_env_value "REDIS_PASSWORD" "$APP_ENV")

if [ -n "$redis_psw" ]; then
    colorEcho blue "\nYou defined a redis password in $APP_ENV. Do you want to secure redis with it (not necessary on local)?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    case $answer in
        "yes")
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
