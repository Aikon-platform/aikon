#!/bin/bash

cd "../app/mediafiles/img" || exit

for file in *.jpg; do
    if ! file "$file" | grep -q "JPEG image data"; then
        echo "Deleting $file because it is not a valid JPEG file."
        rm "$file"
    fi
done
