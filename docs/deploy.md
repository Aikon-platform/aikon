# 🚀 Deploy

## Set up

### Requirements

> - **Sudo** privileges
> - **Python**: 3.10
> - **Java**: 11
> - **Git**: with [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

Clone repository and checkout to production branch
```bash
git clone git@github.com:Aikon-platform/aikon.git
cd aikon && git checkout <your-branch>-prod
```

[//]: # (TODO add Docker documentation + documentation on email setup)

## Manual installation

### Dependencies

Download dependencies
```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt-get install wget ca-certificates
sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql git build-essential poppler-utils redis-server ghostscript
```

Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements-prod.txt
```

### Application

Create postgres database
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE <database-name>;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE <database-name> TO <username>;
postgres=# \q
```

Configure project variables
```bash
cp app/config/.env{.template,}
```

Change variables in the generated file `app/config/.env` to corresponds to your project

Update database schema, create super user and collect static files
```bash
python app/manage.py migrate
python app/manage.py createsuperuser
python app/manage.py collectstatic
```

### Web server: Gunicorn & Nginx

Make sure you can serve app with Gunicorn then quit with Ctrl+C
```bash
gunicorn --bind 0.0.0.0:8000 config.wsgi
```

Create sockets [following this procedure](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04#creating-systemd-socket-and-service-files-for-gunicorn).

The `/etc/systemd/system/gunicorn.service` should look like that
```yaml
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=<production-server-username>
Group=<production-server-group>
WorkingDirectory=<path/to>/config/app
ExecStart=<path/to>/config/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

The `/etc/nginx/sites-available/` directory should contain a config file for nginx named `aikon` for example:
```yaml
server {
    server_name <project-domain-name>;                           # CHANGE HERE

    location /iiif/ {
        proxy_pass http://0.0.0.0:8182/iiif/;
    }

    location /sas/ {
        proxy_ssl_server_name on;
        proxy_set_header        X-Real_IP           $remote_addr;
        proxy_set_header        X-Forwarded-For     $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto   $scheme;
        proxy_set_header        X-NginX-Proxy       true;
        proxy_set_header        Host                $host/sas;
        proxy_set_header        Upgrade             $http_upgrade;
        proxy_pass_header       Set-Cookie;
        proxy_pass              http://0.0.0.0:8888/;
    }

    location /javax.faces.resource/ {
        proxy_pass http://0.0.0.0:8888/javax.faces.resource/;
    }

    location /static/ {
        autoindex off;
        alias </path/to>/app/staticfiles;           # CHANGE HERE
    }

    location /media/ {
        autoindex off;
        alias </path/to>/app/mediafiles/;           # CHANGE HERE
    }

    location / {
        proxy_set_header        X-Real_IP           $remote_addr;
        proxy_set_header        X-Forwarded-For     $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto   $scheme;
        proxy_set_header        X-NginX-Proxy       true;
        proxy_set_header        Host                $http_host;
        proxy_set_header        Upgrade             $http_upgrade;
        proxy_pass_header       Set-Cookie;
        client_max_body_size    5000M;
        proxy_connect_timeout   600;
        proxy_send_timeout      600;
        proxy_read_timeout      600;
        send_timeout            600;
        proxy_pass              http://unix:/run/gunicorn.sock;
    }
}
```

### IIIF image server: Cantaloupe service

Create a .ENV file for cantaloupe
```bash
sudo chmod +x <path/to>/cantaloupe/init.sh && cp <path/to>/cantaloupe/.env{.template,} && nano <path/to>/cantaloupe/.env
```

Modify the variables in order to fit your project:
- `BASE_URI` example: https://eida.obspm.fr
- `FILE_SYSTEM_SOURCE` on prod: `./app/mediafiles/img/`

Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
```bash
<path/to>/cantaloupe/init.sh
```

Create a service for cantaloupe
```bash
sudo vi /etc/systemd/system/cantaloupe.service
```

```
[Unit]
Description=start cantaloupe
After=network.target
After=nginx.service

[Service]
WorkingDirectory=/<absolute/path/to>/aikon/
ExecStart=/<absolute/path/to>/aikon/cantaloupe/start.sh
StandardError=append:/<absolute/path/to>/aikon/cantaloupe/log

[Install]
WantedBy=multi-user.target
```

Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable cantaloupe.service
sudo systemctl start cantaloupe.service
```


### Annotation server: Simple Annotation Server service

Create a service for cantaloupe
```bash
sudo vi /etc/systemd/system/sas.service
```
```
[Unit]
Description=sas service
After=network.target
After=nginx.service

[Service]
User=eida
Group=eida
WorkingDirectory=/<absolute/path/to>/aikon/sas/
ExecStart=/<absolute/path/to>/aikon/sas/start.sh
StandardError=append:/<absolute/path/to>/aikon/sas/error.log

[Install]
WantedBy=multi-user.target
```

Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable sas.service
sudo systemctl start sas.service
```

#### Securing SAS

If you wish to secure access to the annotation server, follow the steps below.

The Simple Annotation Server project does not currently contain authentication,
although it is possible to secure the SAS web application with a single username and password using Nginx forwarding.

Create the password file using the OpenSSL utilities and add a username to the file (corresponding to the one defined in `.env`)
```bash
sudo sh -c "echo -n '<SAS_USERNAME>:' >> /etc/nginx/.htpasswd"
```

Next, add an encrypted password entry for the username
```bash
sudo sh -c "openssl passwd <SAS_PASSWORD> >> /etc/nginx/.htpasswd"
```

You can repeat this process for additional usernames.

To configure Nginx password authentication, open up the server block configuration file and set up authentication
```bash
sudo vi /etc/nginx/sites-enabled/<aikon>
```

```bash
server {
	server_name <project-domain-name>;
	...
	location /sas/ {
        ...
        auth_basic              "Restricted Content";
        auth_basic_user_file    /etc/nginx/.htpasswd;
	}
}
```

Restart Nginx to implement your password policy
```bash
sudo systemctl restart nginx
```

### Celery and Redis

#### Celery
Create a service for Celery
```bash
vi /etc/systemd/system/celery.service
```

```
[Unit]
Description=Celery service
After=network.target
After=nginx.service

[Service]
WorkingDirectory=/<absolute/path/to>/aikon
ExecStart=/<absolute/path/to>/aikon/celery/start.sh
StandardError=append:/<absolute/path/to>/aikon/celery/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery.service
sudo systemctl start celery.service
```

#### Add authentication for Redis
Open the Redis configuration file
```bash
REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
vi $REDIS_CONF
```
Uncomment and set a password (must match the one defined in `.env`)
```
requirepass <REDIS_PASSWORD>
```
Restart Redis
```bash
sudo systemctl restart redis-server
```
Test the password
```bash
redis-cli -a <REDIS_PASSWORD>
```

- [Install VHS on Observatoire servers](https://syrte-int.obspm.fr/dokuwiki/wiki/informatique/prive/eida/installspe#cantaloupe_sas_et_aikon)

# Once the app is deployed...

## Code and files update
On update of the code, you will need to restart gunicorn
```bash
sudo systemctl restart gunicorn.socket
```

On modification of the static files, you will need to restart nginx
then copy static files into `app/staticfiles` in order to be served but nginx
```bash
sudo systemctl restart nginx
python app/manage.py collectstatic
```

To make a command alias, copy that at the end of `~/.bashrc`:
```bash
alias djupdate="sudo systemctl restart gunicorn.socket && sudo systemctl restart nginx"
```

## Data model update
If the data model was changed, you will first need to check that the new data model do not cause any error in the application.
Once the tests performed, a migration file can be generated locally by running:
```bash
python app/manage.py makemigrations
```

It will create a file that tells Django how to modify the Postgres database structure to fit the new model definition.
To apply those modifications, run locally:
```bash
# on local
python app/manage.py migrate
```

If everything is set, update the remote database by running on the production server, once the code has been retrieve from origin:
```bash
# on production
python app/manage.py migrate
```

# Debug

Empty log file by running
```bash
sudo truncate -s 0 /path/to/logfile.log
```
To add aliases to your `.bashrc` config
```bash
vi ~/.bashrc       # paste aliases at the end
source ~/.bashrc   # to activate aliases
```

To activate DEBUG in prod in order to see Django errors (instead of 500 errors)
```bash
# install config/webapp/requirements-dev.txt
vi app/config/.env           # set DEBUG=True
vi app/config/settings.py    # l.87 `if not DEBUG:` => `if DEBUG:`
```
Don't forget to roll back those modifications afterward

## App errors
See `app/logs`

```bash
alias djlog="cat app/logs/<appname>.log"
alias empty_djlog="sudo truncate -s 0 app/logs/<appname>.log"
```

## Nginx error logs
See `/var/log/nginx`

```bash
alias nglog="sudo cat /var/log/nginx/eida.error.log"
alias empty_nglog="sudo truncate -s 0 /var/log/nginx/eida.error.log"
```

## Gunicorn error logs
See `/var/log/gunicorn`: here are python code error that might provoke 502 bad gateway errors

```bash
alias gunilog="sudo cat /var/log/gunicorn/gunicorn-error.log"
alias empty_gunilog="sudo truncate -s 0 /var/log/gunicorn/gunicorn-error.log"
```

## Cantaloupe error logs
See `cantaloupe/log`

```bash
alias cantalog="cat cantaloupe/log"
alias empty_cantalog="sudo truncate -s 0 cantaloupe/log"
```

## SAS error logs
See `sas/log`

```bash
alias slog="cat sas/log"
alias empty_slog="sudo truncate -s 0 sas/log"
```

## Celery error logs
See `celery/log`

```bash
alias celog="cat celery/log"
alias empty_celog="sudo truncate -s 0 celery/log"
```
