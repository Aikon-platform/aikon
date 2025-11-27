#!/bin/env bash

# WHEN TO USE
# Script to clear all migrations files and migration history from database
# Useful when you have uploaded SQL data, changed the models but your migration files do not fit your database

# HOW TO USE
# ⚠️⚠️⚠️ Make sure to commit your code before running the script ⚠️⚠️⚠️
# Inside the scripts/ directory, run:
# bash clear_migration.sh
# Restart Django to see effects

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR"/utils.sh

#options=("yes" "no")
#color_echo blue "\nHave you committed your code before running the script?"
#answer=$(printf "%s\n" "${options[@]}" | fzy)
#
#if [ "$answer" == "no" ]; then
#    color_echo red "Please commit your code before running the script."
#    exit 1
#fi
#
#options=("yes" "no")
#color_echo blue "\nDo you wish to backup database before the script?"
#answer=$(printf "%s\n" "${options[@]}" | fzy)
#
#if [ "$answer" == "yes" ]; then
#    color_echo yellow "\nBacking up the database..."
#    bash "$SCRIPT_DIR/dump_db.sh"
#fi

# Load environment variables from .env file
. "$APP_ROOT"/app/config/.env

db_name=${POSTGRES_DB:-APP_NAME}
db_user=${POSTGRES_USER:-admin}

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

color_echo yellow "\nCreation of a tmp project to generate migrations..."
cd "$SCRIPT_DIR"/ || exit 1;
"$APP_ROOT"/venv/bin/django-admin startproject tmp || exit 1;
cd "$SCRIPT_DIR"/tmp || exit 1;
"$APP_ROOT"/venv/bin/python manage.py startapp webapp || exit 1;
cp "$SCRIPT_DIR"/settings.py.template "$SCRIPT_DIR"/tmp/tmp/settings.py || exit 1;

color_echo yellow "\nClearing migration history from database..."
$command -d "$db_name" -c "TRUNCATE TABLE django_migrations RESTART IDENTITY CASCADE;" || exit 1;

color_echo yellow "\nGenerating models.py out of current database state..."
# Select only table from the webapp app
tables=$($command -d "$db_name" -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'webapp%';" | xargs)
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py inspectdb $tables > webapp/models.py || exit 1;

color_echo yellow "\nAdding app_label to models.py..."
meta_class="    class Meta:"
app_label="\n        app_label = 'webapp'"
sed_repl_inplace "s~^$meta_class~$meta_class$app_label~" webapp/models.py || exit 1;

color_echo yellow "\nCreating migration for the current database state..."
"$APP_ROOT"/venv/bin/python manage.py makemigrations || exit 1;

# Empty the migrations folder
find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' -delete || exit 1;
cp "$SCRIPT_DIR"/tmp/webapp/migrations/0001_initial.py "$APP_ROOT"/app/webapp/migrations/0001_initial.py || exit 1;

#color_echo yellow "\nFaking the application of the initial migration..."
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp || exit 1;

color_echo yellow "\nCreate new migration to mimic the changes in the models"
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations webapp || exit 1;
"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp || exit 1;

color_echo yellow "\nRemoving the tmp project..."
rm -rf "$SCRIPT_DIR"/tmp || exit 1;

color_echo blue "\nMigration process completed successfully! 🎉"
color_echo cyan "Restart Django to see effects"


#color_echo yellow "\nClearing migration history from database..."
#$command -d "$db_name" -c "TRUNCATE TABLE django_migrations RESTART IDENTITY CASCADE;" || exit 1;
#
#color_echo yellow "\nGenerating models.py out of current database state..."
## Select only table from the webapp schema
#tables=$($command -d "$db_name" -t -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'webapp%';" | xargs)
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py inspectdb $tables > "$APP_ROOT"/app/webapp/models.py || exit 1;
#
#color_echo yellow "\nAdding app_label to models.py..."
#meta_class="    class Meta:"
#app_label="\n        app_label = 'webapp'"
#sed_repl_inplace "s~^$meta_class~$meta_class$app_label~" "$APP_ROOT"/app/webapp/models.py || exit 1;
#
#color_echo yellow "\nRename temporary models/ directory..."
#mv "$APP_ROOT"/app/webapp/models "$APP_ROOT"/app/webapp/models_bak || exit 1;
#
#color_echo yellow "\nDeleting all migrations files..."
#find "$APP_ROOT"/app/webapp/migrations -type f ! -name '__init__.py' -delete || exit 1;
#
#color_echo yellow "\nCreating migration for the current database state..."
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations webapp || exit 1;
#
#color_echo yellow "\nFaking the application of the initial migration..."
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate webapp --fake || exit 1;
#
#color_echo yellow "\nRemoving the generated models file and restoring the original models directory..."
#rm "$APP_ROOT"/app/webapp/models.py || exit 1;
#mv "$APP_ROOT"/app/webapp/models_bak "$APP_ROOT"/app/webapp/models || exit 1;
#
#color_echo yellow "\nCreate new migration to mimic the changes in the models!"
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py makemigrations
#"$APP_ROOT"/venv/bin/python "$APP_ROOT"/app/manage.py migrate
#
#color_echo blue "\nMigration process completed successfully! 🎉"
#color_echo cyan "Restart Django to see effects"
