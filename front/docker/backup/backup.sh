DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT/scripts/utils.sh"
source "$DOCKER_DIR/.env"

run_script backup_code.sh "Backup current code"
run_script backup_files.sh "Backup mediafiles and sas annotations"
run_script backup_data.sh "Backup SQL of db container"
