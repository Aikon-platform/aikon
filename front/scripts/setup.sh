#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_DIR="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/functions.sh

run_script() {
    local script_name="$1"
    local description="$2"
    local install_type="$3"
    options=("yes" "no")

    color_echo blue "Do you want to run $description ?"
    answer=$(printf "%s\n" "${options[@]}" | fzy)
    echo ""
    case $answer in
        "yes")
            # only pass $install_type to $scrit_name if $script_name is in $pass_install_type
            pass_install_type=("setup_var_env.sh" "setup_cantaloupe.sh" "setup_redis.sh")
            extra_param=$([[ " ${pass_install_type[*]} " =~ "$script_name" ]] && echo "$install_type" || echo "" )

            bash "$SCRIPT_DIR/$script_name" "$extra_param" \
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
case $OS in
    Linux)
        sudo apt install fzy
        ;;
    Mac)
        brew install fzy
        ;;
    *)
        color_echo red "Unsupported OS: $OS"
        exit 1
        ;;
esac


color_echo blue "Do you want to run a full install or a quick install (skips defining basic env variables, perfect for dev) ?"
options=("quick install" "full install")
answer=$(printf "%s\n" "${options[@]}" | fzy)
INSTALL_TYPE="${answer/ /_}"  # "quick_install" or "full_install", will default to "full_install"
color_echo blue "Running a $answer !"

run_script setup_system_packages.sh "Submodule initialization" "$INSTALL_TYPE"
run_script setup_venv.sh "Virutal environment initialization" "$INSTALL_TYPE"
run_script setup_var_env.sh "Environment variables configuration" "$INSTALL_TYPE"
run_script setup_cantaloupe.sh "Cantaloupe configuration" "$INSTALL_TYPE"
run_script setup_db.sh "Database generation" "$INSTALL_TYPE"
run_script setup_webpack.sh "Webpack initialization" "$INSTALL_TYPE"
run_script setup_redis.sh "Redis password configuration" "$INSTALL_TYPE"
# run_script setup_sas.sh "SAS initialization" "$INSTALL_TYPE"

echo_title "🎉 ALL SET UP! 🎉"
color_echo blue "\nYou can now run the server with: "
color_echo cyan "              bash run.sh"
