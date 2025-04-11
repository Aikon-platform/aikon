source "$TARGET_APP_ROOT/scripts/utils.sh"
echo_title "SAS ANNOTATIONS DUPLICATION"

SOURCE_SAS_DIR="$SOURCE_APP_ROOT/sas/data"
if [ ! -d "$SOURCE_SAS_DIR" ]; then
    error "SAS data directory not found at $SOURCE_SAS_DIR"
fi
TARGET_SAS_DIR="$DATA_FOLDER/sas"
if [ ! -d "$TARGET_SAS_DIR" ]; then
    mkdir -p "$TARGET_SAS_DIR" || error "Failed to create SAS data directory"
    chmod 755 "$TARGET_SAS_DIR"
fi

color_echo cyan "Source SAS directory: $SOURCE_SAS_DIR"
color_echo cyan "Target SAS directory: $TARGET_SAS_DIR"

if [ "$SOURCE_SAS_DIR" = "$TARGET_SAS_DIR" ]; then
    color_echo yellow "Source and destination SAS directories match! No need to copy data."
else
    SOURCE_SIZE=$(du -s "$SOURCE_SAS_DIR" | awk '{print $1}')
    TARGET_SIZE=$(du -s "$TARGET_SAS_DIR" | awk '{print $1}')

    if [ -d "$TARGET_SAS_DIR" ] && [ $SOURCE_SIZE -eq $TARGET_SIZE ]; then
        color_echo yellow "Source and target SAS directories have similar sizes. Skipping copy."
    else
        color_echo yellow "Rsyncing existing SAS data from $SOURCE_SAS_DIR to $TARGET_SAS_DIR"
        rsync -av --progress "$SOURCE_SAS_DIR/" "$TARGET_SAS_DIR/" || error "Failed to copy SAS data"
    fi
fi

ask "Do you want to check that annotations are well accessed by SAS container?"
docker start $SAS_CONTAINER || error "Failed to start SAS container"
color_echo yellow "Waiting for SAS container to start..."
sleep 10

color_echo cyan "Content of $TARGET_SAS_DIR"
SAS_VOLUME_FILES=$(ls -A "$TARGET_SAS_DIR")
ls "$SAS_VOLUME_FILES"

color_echo cyan "Content of $SAS_CONTAINER:/sas/data"
SAS_DOCKER_FILES=$(docker exec -i "$SAS_CONTAINER" ls -A /sas/data)
ls "$SAS_DOCKER_FILES"

# if [ ! "$SAS_VOLUME_FILES" = "$SAS_DOCKER_FILES" ]; then
#     color_echo yellow "Content of SAS container data does not match mounted volume. Copying data into container..."
#     find "$TARGET_SAS_DIR" -type f -print0 | tar -c --null -T - | docker exec -i "$SAS_CONTAINER" tar -x -C /sas/data
#     color_echo yellow "SAS data copied to container successfully"
# fi
