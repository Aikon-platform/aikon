#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/functions.sh

run_script() {
    local script_name="$1"
    local description="$2"
    options=("yes" "no")

    color_echo blue "Do you want to run $description ?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    case $answer in
        "yes")
            bash "$SCRIPT_DIR/$script_name" \
            && color_echo green "$description completed successfully" \
            || color_echo red "$description failed with exit code. Continuing..."
            ;;
        *)
            color_echo blue "Skipping $description"
            ;;
    esac
    echo ""
}

color_echo blue "\nInstalling prompt utility fzy..."
if [ "$OS" = "Linux" ]; then
    sudo apt install fzy
elif [ "$OS" = "Mac" ]; then
    brew install fzy
else
    color_echo red "Unsupported OS: $OS"
    exit 1
fi

INSTALL_MODE="full_install"
choose_install_mode() {
    color_echo blue "Do you want to run a full install or a quick install (skips defining basic env variables, perfect for dev)?"
    options=("quick install" "full install")
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    INSTALL_MODE="${answer/ /_}"  # "quick_install" or "full_install", will default to "full_install"
    export INSTALL_MODE="$INSTALL_MODE"
    color_echo blue "Running a $answer!"
}
choose_install_mode

run_script setup_system_packages.sh "Submodule initialization"
run_script setup_venv.sh "Virtual environment initialization"
run_script setup_var_env.sh "Environment variables configuration"
run_script setup_cantaloupe.sh "Cantaloupe configuration"
run_script setup_db.sh "Database generation"
run_script setup_webpack.sh "Webpack initialization"
# run_script setup_redis.sh "Redis password configuration"
# run_script setup_sas.sh "SAS initialization"

echo_title "🎉 ALL SET UP! 🎉"
color_echo blue "\nYou can now run the server with: "
color_echo cyan "              bash run.sh"
