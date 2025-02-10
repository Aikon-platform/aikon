#!/bin/bash

# HOW TO USE
# Disable superuser identification for index-annotation view
# In the script directory
# ./rename.sh

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$APP_ROOT"/app/config/.env

. "$ENV_FILE"

PREFIXES=("ms" "tpr" "wpr")
IMG_DIR="$APP_ROOT"/app/mediafiles/img
REGIONS_DIR="$APP_ROOT"/app/mediafiles/regions

for PREFIX in "${PREFIXES[@]}"; do
    for FILE_PATH in "$IMG_DIR/${PREFIX}"*; do
        if [ -e "$FILE_PATH" ]; then
            ID=$(basename "$FILE_PATH" | sed "s/${PREFIX}\([0-9]\+\)_.*$/\1/")

            NEW_IMG_NAME="wit${ID}_$(basename "$FILE_PATH" | sed "s/${PREFIX}${ID}_//")"

            mv "$FILE_PATH" "$IMG_DIR/$NEW_IMG_NAME"
        else
            echo "No image file for $FILE_PATH"
        fi
    done
done

for PREFIX in "${PREFIXES[@]}"; do
    for REGIONS_PATH in "$REGIONS_DIR/${PREFIX}"*.txt; do
        if [ -e "$REGIONS_PATH" ]; then
            ID=$(basename "$REGIONS_PATH" | sed "s/${PREFIX}\([0-9]\+\)_.*$/\1/")

            REGIONS_CONTENT=$(basename "$REGIONS_PATH" | sed "s/${PREFIX}${ID}_\(.*\).txt/\1/")

            NEW_REGIONS_NAME="wit${ID}_${REGIONS_CONTENT}"

            mv "$REGIONS_PATH" "$REGIONS_DIR/${NEW_REGIONS_NAME}.txt"

            sed -i "s/${PREFIX}${ID}_/wit${ID}_/" "$REGIONS_DIR/${NEW_REGIONS_NAME}.txt"

            echo "Rewrote $REGIONS_PATH"

            # Reindex in SAS
            URL="https://$PROD_URL/$APP_NAME/index-annotation/$NEW_REGIONS_NAME"
            echo "URL: $URL"
            curl -sS "$URL"

        else
            echo "No annotation file for $REGIONS_PATH"
        fi
    done
done
