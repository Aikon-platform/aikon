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
ANNOTATION_DIR="$APP_ROOT"/app/mediafiles/annotation

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
    for ANNOTATION_PATH in "$ANNOTATION_DIR/${PREFIX}"*.txt; do
        if [ -e "$ANNOTATION_PATH" ]; then
            ID=$(basename "$ANNOTATION_PATH" | sed "s/${PREFIX}\([0-9]\+\)_.*$/\1/")

            ANNOTATION_CONTENT=$(basename "$ANNOTATION_PATH" | sed "s/${PREFIX}${ID}_\(.*\).txt/\1/")

            NEW_ANNOTATION_NAME="wit${ID}_${ANNOTATION_CONTENT}"

            mv "$ANNOTATION_PATH" "$ANNOTATION_DIR/${NEW_ANNOTATION_NAME}.txt"

            sed -i "s/${PREFIX}${ID}_/wit${ID}_/" "$ANNOTATION_DIR/${NEW_ANNOTATION_NAME}.txt"

            echo "Rewrote $ANNOTATION_PATH"

            # Reindex in SAS
            URL="https://$PROD_URL/$APP_NAME/index-annotation/$NEW_ANNOTATION_NAME"
            echo "URL: $URL"
            curl -sS "$URL"

        else
            echo "No annotation file for $ANNOTATION_PATH"
        fi
    done
done
