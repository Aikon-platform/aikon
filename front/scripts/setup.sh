#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/functions.sh

OS=$(get_os)

run_script() {
    local script_name="$1"
    local description="$2"
    options=("yes" "no")

    colorEcho blue "Do you want to run $description ?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    case $answer in
        "yes")
            bash "$SCRIPT_DIR/$script_name"
            && colorEcho green "$description completed successfully"
            || colorEcho red "$description failed with exit code. Continuing..."
            ;;
        *)
            colorEcho blue "Skipping $description"
            ;;
    esac
}

colorEcho blue "\nInstalling prompt utility fzy..."
case $OS in
    Linux)
        sudo apt install fzy
        ;;
    Mac)
        brew install fzy
        ;;
    *)
        colorEcho red "Unsupported OS: $os"
        exit 1
        ;;
esac

run_script setup_install_packages.sh "Submodule initialization"
run_script setup_venv.sh "Virutal environment initialization"
run_script setup_var_env.sh "Environment variables configuration"
run_script setup_cantaloupe.sh "Cantaloupe configuration"
run_script setup_db.sh "Database generation"
run_script setup_webpack.sh "Webpack initialization"
run_script setup_redis.sh "Redis password configuration"
# run_script setup_sas.sh "SAS initialization"

echoTitle "🎉 ALL SET UP! 🎉"
colorEcho blue "\nYou can now run the server with: "
colorEcho cyan "              bash run.sh"
