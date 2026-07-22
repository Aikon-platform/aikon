CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$CURRENT_DIR")"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"
source "$DOCKER_DIR/.env"

# Source and target data folders can either be:
# - a local folder (e.g. /path/to/data)
# - a distant folder (e.g. ssh_host:/path/to/data)
#   when using a distant folder, the ssh_host must already been configured in ~/ssh/config + SSH key pair
SOURCE_FOLDER="$DATA_DIR"
TARGET_FOLDER="$DATA_BACKUP" # ${DATA_BACKUP:-"/data/aikon_backup"}

if [ ! -d "$SOURCE_FOLDER" ]; then
    echo "Source data folder $SOURCE_FOLDER does not exist. Exiting"
    exit 1
fi

if [ "$TARGET_FOLDER" = "" ]; then
    read -p "Enter the path where to create backup: " TARGET_FOLDER
fi

if [ ! -d "$TARGET_FOLDER" ]; then
    mkdir -p "$TARGET_FOLDER"
fi

ME=$(whoami)
MY_GROUP=$(id -gn)

backup_files() {
    SOURCE_DIR=$1
    TARGET_DIR=$2

    TODAY=$(date +%Y-%m-%d)
    LOG_FILE="${TARGET_DIR}/backup_log_${TODAY}.txt"

    echo "Backup started at $(date)" > "${LOG_FILE}"

    # Run rsync with the following options:
    # -a = archive mode: preserves permissions, timestamps, symbolic links, etc.
    # -v = verbose: shows files being copied
    # -z = compression: compresses data during transfer
    # --update = only copy newer files
    # -e ssh = specify ssh as the remote shell
    rsync -avz --update -e ssh "$SOURCE_DIR" "$TARGET_DIR" >> "${LOG_FILE}" 2>&1

    chown -R ${ME}:${MY_GROUP} "${TARGET_DIR}"
    echo "Backup completed at $(date)" >> "${LOG_FILE}"
}

backup_files "$SOURCE_FOLDER" "$TARGET_FOLDER"
