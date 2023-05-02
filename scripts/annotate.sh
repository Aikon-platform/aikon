#!/bin/bash

# HOW TO USE
# in the script directory
# sh annotate.sh filename.txt
# filename.txt -> each line is a manifest URL from eida

# function to print colored output
colorEcho () {
    Color_Off="\033[0m"
    Red="\033[1;91m"        # Red
    Green="\033[1;92m"      # Green
    Yellow="\033[1;93m"     # Yellow
    Blue="\033[1;94m"       # Blue
    Purple="\033[1;95m"     # Purple
    Cyan="\033[1;96m"       # Cyan
    case "$1" in
        "success") echo "$Green$2$Color_Off";;
        "error") echo "$Red$2$Color_Off";;
        "log") echo "$Yellow$2$Color_Off";;
        "info") echo "$Blue$2$Color_Off";;
        "warning") echo "$Purple$2$Color_Off";;
        "message") echo "$Cyan$2$Color_Off";;
        *) echo "$2";;
    esac
}

if test "$#" -ne 1; then
    colorEcho "error" "Usage: $0 <input-file-path>"
fi

input_file=$1
file_name=$(basename -- "${input_file%.*}")

echo "$(figlet ANNOTATOR)"

colorEcho "info" "Copying $input_file to dishas-ia ..."
scp "$input_file" dishas-ia:yolov5/manifests/ || colorEcho "error" "Failed to copy file to dishas-ia"

colorEcho "info" "Launching detection..."
ssh -t dishas-ia "cd yolov5 && vhs/bin/python detect_vhs.py -f manifests/$file_name.txt" || colorEcho "error" "Failed to run detection"

colorEcho "info" "Content of the output directory:"
ssh eida "ls yolov5/output/"

colorEcho "info" "Copying output files to eida server..."
scp dishas-ia:yolov5/output/* eida:vhs/vhs-platform/mediafiles/manuscripts/annotation/ || colorEcho "error" "Failed to copy output files to eida server"
scp dishas-ia:yolov5/output/* ../vhs-platform/mediafiles/manuscripts/annotation/ || colorEcho "error" "Failed to copy output files to local app"

colorEcho "log" "Content of the annotation directory:"
ssh eida "ls vhs/vhs-platform/mediafiles/manuscripts/annotation/"
