#!/bin/bash

# HOW TO USE
# sh annotate.sh filename.txt
# filename.txt -> each line is a manifest URL from eida

# function to print colored output
colorEcho () {
    case "$1" in
        "success") echo -e "\033[32m$2\033[0m";;
        "error") echo -e "\033[31m$2\033[0m";;
        *) echo "$2";;
    esac
}

error () {
    colorEcho "error" "ERROR: $1"
    exit 1
}

if test "$#" -ne 1; then
    error "Usage: $0 <input-file-path>"
fi

input_file=$1
file_name=$(basename -- "${input_file%.*}")

echo "$(figlet ANNOTATOR)"

colorEcho "info" "Copying $input_file to dishas-ia ..."
scp "$input_file" dishas-ia:yolov5/manifests/ || error "Failed to copy file to dishas-ia"

colorEcho "info" "Launching detection..."
ssh -t dishas-ia "cd yolov5 && vhs/bin/python detect_vhs.py -f manifests/$file_name.txt" || error "Failed to run detection"

colorEcho "info" "Content of the output directory:"
ssh eida "ls yolov5/output/"

colorEcho "info" "Copying output files to eida server ..."
scp dishas-ia:yolov5/output/* eida:vhs/vhs-platform/mediafiles/manuscripts/annotation/ || error "Failed to copy output files to eida server"

colorEcho "success" "All steps completed successfully."

colorEcho "info" "Content of the annotation directory:"
ssh eida "ls vhs/vhs-platform/mediafiles/manuscripts/annotation/"
