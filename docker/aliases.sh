#!/bin/bash

# Paths for aliases and functions
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

add_if_not_exists() {
    local entry="$1"
    local file="$2"

    if ! grep -qF "$entry" "$file"; then
        echo "$entry" >> "$file"
    fi
}

BASHRC_FILE="$HOME/.bashrc"

git_branch_func="git_branch() {
    if [ -d .git ] || git rev-parse --git-dir > /dev/null 2>&1; then
        echo $(git branch 2>/dev/null | grep '^*' | colrm 1 2)
    fi
}"

alias_gdiff="alias gdiff='git fetch && git diff \$(git_branch) origin/\$(git_branch) -- \":(exclude)$APP_ROOT/app/webapp/static/svelte/\"'"
alias_aikon="alias aikon='cd $APP_ROOT/docker && docker compose'"
alias_static="alias static='aikon exec web /home/aikon/venv/bin/python /home/aikon/app/manage.py collectstatic --noinput'"
alias_log="alias log='aikon exec web tail -n 150 -f /home/aikon/app/logs/app_log.log'"

add_if_not_exists "$git_branch_func" "$BASHRC_FILE"
add_if_not_exists "$alias_gdiff" "$BASHRC_FILE"
add_if_not_exists "$alias_aikon" "$BASHRC_FILE"
add_if_not_exists "$alias_static" "$BASHRC_FILE"
add_if_not_exists "$alias_log" "$BASHRC_FILE"

source "$BASHRC_FILE"
