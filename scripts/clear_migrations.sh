#!/bin/bash

# WHEN TO USE
# Script to clear all migrations files and migration history from database
# Useful when you have uploaded SQL data, changed the models but your migration files do not fit your database

# HOW TO USE
# ⚠️⚠️⚠️ Make sure to commit your code before running the script ⚠️⚠️⚠️
# Inside the scripts/ directory, run:
# bash clear_migration.sh
# Restart Django to see effects

colorEcho() {
    Color_Off="\033[0m"
    Red="\033[1;91m"        # Red
    Green="\033[1;92m"      # Green
    Yellow="\033[1;93m"     # Yellow
    Blue="\033[1;94m"       # Blue
    Purple="\033[1;95m"     # Purple
    Cyan="\033[1;96m"       # Cyan

    case "$1" in
        "green") echo -e "$Green$2$Color_Off";;
        "red") echo -e "$Red$2$Color_Off";;
        "blue") echo -e "$Blue$2$Color_Off";;
        "yellow") echo -e "$Yellow$2$Color_Off";;
        "purple") echo -e "$Purple$2$Color_Off";;
        "cyan") echo -e "$Cyan$2$Color_Off";;
        *) echo "$2";;
    esac
}

get_os() {
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     os=Linux;;
        Darwin*)    os=Mac;;
        CYGWIN*)    os=Cygwin;;
        MINGW*)     os=MinGw;;
        MSYS_NT*)   os=Git;;
        *)          os="UNKNOWN:${unameOut}"
    esac
    echo "${os}"
}

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

#options=("yes" "no")
#colorEcho blue "\nHave you committed your code before running the script?"
#answer=$(printf "%s\n" "${options[@]}" | fzy)
#
#if [ "$answer" == "no" ]; then
#    colorEcho red "Please commit your code before running the script."
#    exit 1
#fi
#
#options=("yes" "no")
#colorEcho blue "\nDo you wish to backup database before the script?"
#answer=$(printf "%s\n" "${options[@]}" | fzy)
#
#if [ "$answer" == "yes" ]; then
#    colorEcho yellow "\nBacking up the database..."
#    bash "$SCRIPT_DIR/dump_db.sh"
#fi

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

db_name=${DB_NAME:-APP_NAME}
db_user=${DB_USERNAME:-admin}

case $(get_os) in
    Linux)
        command="sudo -i -u $db_user psql"
        ;;
    Mac)
        command="psql -U $db_user"
        ;;
    *)
        echo "Unsupported OS: you need to create the database manually"
        exit 1
        ;;
esac

colorEcho yellow "\nCreation of a tmp project to generate migrations..."
cd "$SCRIPT_DIR"/ || exit 1;
"$APP_ROOT"/venv/bin/django-admin startproject tmp || exit 1;
cd "$SCRIPT_DIR"/tmp || exit 1;
"$APP_ROOT"/venv/bin/python manage.py startapp webapp || exit 1;
cp "$SCRIPT_DIR"/settings.py.template "$SCRIPT_DIR"/tmp/tmp/settings.py || exit 1;

colorEcho yellow "\nClearing migration history from database..."
$command -d "$db_name" -c "TRUNCATE TABLE django_migrations RESTART IDENTITY CASCADE;" || exit 1;

colorEcho yellow "\nGenerating models.py out of current database state..."
# Select only table from the webapp app
tables=$($command -d "$db_name" -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'webapp%';" | xargs)
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py inspectdb $tables > webapp/models.py || exit 1;

colorEcho yellow "\nAdding app_label to models.py..."
meta_class="    class Meta:"
app_label="\n        app_label = 'webapp'"
sed -i "" -e "s~^$meta_class~$meta_class$app_label~" webapp/models.py || exit 1;

colorEcho yellow "\nCreating migration for the current database state..."
"$APP_ROOT"/venv/bin/python manage.py makemigrations || exit 1;

# Empty the migrations folder
find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' -delete || exit 1;
cp "$SCRIPT_DIR"/tmp/webapp/migrations/0001_initial.py "$APP_ROOT"/app/webapp/migrations/0001_initial.py || exit 1;

#colorEcho yellow "\nFaking the application of the initial migration..."
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp || exit 1;

colorEcho yellow "\nCreate new migration to mimic the changes in the models"
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations webapp || exit 1;
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp || exit 1;

colorEcho yellow "\nRemoving the tmp project..."
rm -rf "$SCRIPT_DIR"/tmp || exit 1;

colorEcho blue "\nMigration process completed successfully! 🎉"
colorEcho cyan "Restart Django to see effects"


#colorEcho yellow "\nClearing migration history from database..."
#$command -d "$db_name" -c "TRUNCATE TABLE django_migrations RESTART IDENTITY CASCADE;" || exit 1;
#
#colorEcho yellow "\nGenerating models.py out of current database state..."
## Select only table from the webapp schema
#tables=$($command -d "$db_name" -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'webapp%';" | xargs)
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py inspectdb $tables > "$APP_ROOT"/app/webapp/models.py || exit 1;
#
#colorEcho yellow "\nAdding app_label to models.py..."
#meta_class="    class Meta:"
#app_label="\n        app_label = 'webapp'"
#sed -i "" -e "s~^$meta_class~$meta_class$app_label~" "$APP_ROOT"/app/webapp/models.py || exit 1;
#
#colorEcho yellow "\nRename temporary models/ directory..."
#mv "$APP_ROOT"/app/webapp/models "$APP_ROOT"/app/webapp/models_bak || exit 1;
#
#colorEcho yellow "\nDeleting all migrations files..."
#find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' -delete || exit 1;
#
#colorEcho yellow "\nCreating migration for the current database state..."
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations webapp || exit 1;
#
#colorEcho yellow "\nFaking the application of the initial migration..."
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp --fake || exit 1;
#
#colorEcho yellow "\nRemoving the generated models file and restoring the original models directory..."
#rm "$APP_ROOT"/app/webapp/models.py || exit 1;
#mv "$APP_ROOT"/app/webapp/models_bak "$APP_ROOT"/app/webapp/models || exit 1;
#
#colorEcho yellow "\nCreate new migration to mimic the changes in the models!"
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate
#
#colorEcho blue "\nMigration process completed successfully! 🎉"
#colorEcho cyan "Restart Django to see effects"
