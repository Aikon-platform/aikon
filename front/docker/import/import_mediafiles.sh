echo_title "MEDIAFILES LINKING"
source "$DOCKER_DIR/.env"

source "$TARGET_APP_ROOT/scripts/utils.sh"

DOCKER_ENV_FILE="$DOCKER_DIR/.env"
if [ ! -f "$DOCKER_ENV_FILE" ]; then
    error "Environment file not found at $DOCKER_ENV_FILE"
fi
SOURCE_MEDIA_DIR=$MEDIA_DIR
TARGET_MEDIA_DIR="$DATA_FOLDER/mediafiles"

color_echo cyan "Source media directory: $SOURCE_MEDIA_DIR"
color_echo cyan "Target media directory: $TARGET_MEDIA_DIR"

if [ "$SOURCE_MEDIA_DIR" = "$TARGET_MEDIA_DIR" ]; then
    color_echo yellow "Source and destination media directories match! No need to link."
else
    color_echo yellow "Linking existing media files from $SOURCE_MEDIA_DIR to $TARGET_MEDIA_DIR"
    ln -s "$SOURCE_MEDIA_DIR"/* "$TARGET_MEDIA_DIR"/ || error "Failed to symlink mediafiles/"
    # rsync -av --progress "$SOURCE_MEDIA_DIR/" "TARGET_MEDIA_DIR/" || error "Failed to copy media files"
fi
