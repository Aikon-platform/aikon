CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$(dirname "$CURRENT_DIR")"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"
source "$DOCKER_DIR/.env"

function git_branch() {
    if [ -d .git ] || git rev-parse --git-dir > /dev/null 2>&1; then
        local branch_name=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)

        if [ -n "$branch_name" ]; then
            echo "$branch_name"
        fi
    fi
}

PROD_BRANCH=${PROD_BRANCH:-$(git_branch)}

if [ "$PROD_BRANCH" = "" ]; then
    echo "Branch name is not defined or not in a repository. Exiting"
    exit 1
fi

backup_code() {
    git branch -d "${PROD_BRANCH}_legacy" 2>/dev/null || true
    git switch -c "${PROD_BRANCH}_legacy"
    git push -u origin "${PROD_BRANCH}_legacy" || {
        echo "Failed to push legacy branch to remote"
        exit 1
    }
    git switch $PROD_BRANCH
}

backup_code
