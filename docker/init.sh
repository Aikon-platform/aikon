DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$DOCKER_DIR")"

source "$APP_ROOT"/scripts/functions.sh

# if ../app/config/.env does not exist, create it
if [ ! -f "$APP_ROOT"/app/config/.env ]; then
    cp "$APP_ROOT"/app/config/.env.template "$APP_ROOT"/app/config/.env
    update_env "$APP_ROOT"/app/config/.env
fi

# if ../cantaloupe/.env does not exist, create it
if [ ! -f "$APP_ROOT"/cantaloupe/.env ]; then
    cp "$APP_ROOT"/cantaloupe/.env.template "$APP_ROOT"/cantaloupe/.env
    update_cantaloupe_env
    bash "$APP_ROOT"/cantaloupe/init.sh
fi

# if docker/.env does not exist, create it
if [ ! -f "$APP_ROOT"/docker/.env ]; then
    cp "$APP_ROOT"/docker/.env.template "$APP_ROOT"/docker/.env
    update_env "$APP_ROOT"/docker/.env
fi

source "$APP_ROOT"/app/config/.env
# TODO redis password

source "$APP_ROOT"/docker/.env
# Create $DATA_FOLDER folder with right permissions for user $USERID
sudo mkdir -p "$DATA_FOLDER"
sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
sudo chmod -R 775 "$DATA_FOLDER"
