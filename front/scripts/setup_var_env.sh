SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR=$(dirname "$SCRIPT_DIR")
APP_ENV="$FRONT_DIR"/app/config/.env

source "$SCRIPT_DIR"/functions.sh

echoTitle "APP ENV GENERATION"

cp "$APP_ENV".template "$APP_ENV"
update_env "$APP_ENV"
