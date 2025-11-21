#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$(dirname "$SCRIPT_DIR")"

INSTALL_MODE=${INSTALL_MODE:-"full_install"}
source "$SCRIPT_DIR"/utils.sh

color_echo cyan "Running a $INSTALL_MODE for the front app! 🚀"

color_echo blue "\nInstalling prompt utility fzy..."
if [ "$OS" = "Linux" ]; then
    sudo apt install fzy
elif [ "$OS" = "Mac" ]; then
    brew install fzy
else
    color_echo red "Unsupported OS: $OS"
    exit 1
fi

run_script setup_system_packages.sh "System package install"
run_script setup_venv.sh "Virtual environment initialization"
run_script setup_var_env.sh "Environment variables configuration"
run_script setup_cantaloupe.sh "Cantaloupe configuration"
run_script setup_db.sh "Database generation"
run_script setup_webpack.sh "Webpack initialization"
run_script setup_redis.sh "Redis configuration"
run_script setup_mongodb.sh "MongoDB installation"
# run_script setup_aiiinotate.sh "Aiiinotate initialization"

echo_title "🎉 DJANGO APP IS SET UP! 🎉"
color_echo blue "\nYou can now run the server with: "
color_echo cyan "              bash run.sh"
