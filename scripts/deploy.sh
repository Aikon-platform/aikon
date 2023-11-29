#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

# Deploy Script for VHS App
. "$APP_ROOT"/app/config/.env

# Requirements
sudo apt update
sudo apt-get install -y wget ca-certificates
sudo apt-get install -y python3-venv python3-dev libpq-dev nginx curl maven postgresql git build-essential poppler-utils redis-server ghostscript

# Set up virtual environment
python3 -m venv venv
source "$APP_ROOT"/venv/bin/activate
pip install -r "$APP_ROOT"/app/requirements-prod.txt

# Create PostgreSQL database
sudo -u postgres psql
# PostgreSQL commands: CREATE DATABASE, CREATE USER, ALTER ROLE, GRANT PRIVILEGES
# \q to exit

# Configure project variables
cp "$APP_ROOT"/app/config/.env{.template,}
# Modify "$APP_ROOT"/app/config/.env file with project variables

# Update database schema, create superuser, and collect static files
python "$APP_ROOT"/app/manage.py migrate
python "$APP_ROOT"/app/manage.py createsuperuser
python "$APP_ROOT"/app/manage.py collectstatic

# Image servers - Cantaloupe
chmod +x "$APP_ROOT"/cantaloupe/init.sh
cp "$APP_ROOT"/cantaloupe/.env{.template,}
nano "$APP_ROOT"/cantaloupe/.env
# Modify Cantaloupe .env file with project variables
$APP_ROOT/cantaloupe/init.sh

# Create service for Cantaloupe
sudo vi /etc/systemd/system/cantaloupe.service
# Add Cantaloupe service configuration
# Save and exit

# Launch SAS
cd "$APP_ROOT"/sas && mvn jetty:run

# Set up Nginx password authentication
sudo sh -c "echo -n '<username>:' >> /etc/nginx/.htpasswd"
sudo sh -c "openssl passwd <password> >> /etc/nginx/.htpasswd"

# Configure Nginx server block
sudo vi /etc/nginx/sites-enabled/vhs
# Add Nginx server block configuration
# Save and exit

# Restart Nginx
sudo systemctl restart nginx

# Create service for Celery
vi /etc/systemd/system/celery.service
# Add Celery service configuration
# Save and exit

# Reload systemd manager configuration
sudo systemctl daemon-reload

# Enable authentication for Redis instance
vi /etc/redis/redis.conf
# Uncomment and set a password
# Save and exit
sudo systemctl restart redis-server

echo "Deployment completed successfully."
