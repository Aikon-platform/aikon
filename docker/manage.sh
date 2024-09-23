#!/bin/bash

set -e

source /home/aikon/app/config/.env

# wait 2sec for postgres to start
sleep 2

/home/aikon/venv/bin/python /home/aikon/app/manage.py collectstatic --noinput

/home/aikon/venv/bin/python /home/aikon/app/manage.py makemigrations
/home/aikon/venv/bin/python /home/aikon/app/manage.py migrate

# Create superuser if it doesn't exist
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
username = '$POSTGRES_USER';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, '$CONTACT_MAIL', '$POSTGRES_PASSWORD');
    print('Superuser created.');
else:
    print('Superuser already exists.');
" | /home/aikon/venv/bin/python /home/aikon/app/manage.py shell
