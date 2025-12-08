#!/bin/bash

set -e

manage="/home/aikon/venv/bin/python /home/aikon/app/manage.py"

# wait 2sec for postgres to start
sleep 2

$manage collectstatic --noinput

#$manage makemigrations
#$manage migrate

# source /home/aikon/app/config/.env
# # Create superuser if it doesn't exist
# echo "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# username = '$POSTGRES_USER';
# if not User.objects.filter(username=username).exists():
#     User.objects.create_superuser(username, '$EMAIL_HOST_USER', '$POSTGRES_PASSWORD');
#     print('Superuser created.');
# else:
#     print('Superuser already exists.');
# " | /home/aikon/venv/bin/python /home/aikon/app/manage.py shell
