#!/bin/env bash

set -e

manage="uv --directory=/home/aikon/app run /home/aikon/app/manage.py"

$manage collectstatic --noinput

$manage migrate

$manage create_superuser_check
