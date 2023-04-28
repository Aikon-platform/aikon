## 🚀 Deploy

### Requirements

> - **Sudo** privileges
> - **Python**: 3.10
> - **Java**: 11
> - **Git**: with [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

Download dependencies
```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt-get install wget ca-certificates
sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql git build-essential
```

### Set up

Clone repository and checkout to branch
```bash
git clone git@github.com:faouinti/vhs.git
cd vhs && git checkout vhs-prod
```

Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r vhs-platform/requirements-prod.txt
```

Create prostgres database
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE <database-name>;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE vhs TO <username>;
postgres=# \q
```

Configure project variables
```bash
cp vhs-platform/vhs/.env{.template,}
```

Change variables in the generated file `vhs-platform/vhs/.env` to corresponds to your project
```bash
ALLOWED_HOSTS="localhost,127.0.0.1,145.238.203.8"  # add the domain name used on prod, e.g. "eida.obspm.fr"
SECRET_KEY="<secret-key>"            # random string of characters
DEBUG=True                           # set to False on prod
DB_NAME="<database-name>"            # database name you defined
DB_USERNAME="<database-username>"    # database username you defined
DB_PASSWORD="<database-password>"    # database password you defined
DB_HOST="<database-host>"            # localhost
DB_PORT="<database-port>"            # 5432
SAS_USERNAME="<sas-username>"
SAS_PASSWORD="<sas-password>"
GPU_REMOTE_HOST="<gpu-host>"
GPU_USERNAME="<gpu-username>"
GPU_PASSWORD="<gpu-password>"
PROD_URL="<url-used-for-prod>"       # e.g. "https://eida.obspm.fr"
APP_NAME="<app-name-lowercase>"      # name of the application, e.g. "eida"
GEONAMES_USER="<geonames-username>"  # same username as the one defined on local
APP_LANG="<fr-or-en>"                # lang to be used in the app: work either for french (fr) or english (en)
```

Update database schema, create super user and collect static files
```bash
./venv/bin/python vhs-platform/manage.py migrate
./venv/bin/python vhs-platform/manage.py createsuperuser
./venv/bin/python vhs-platform/manage.py collectstatic
```

Create exception for port 8000
```shell
sudo ufw allow 8000
```

Change app name in `vhs-platform/vhsapp/utils/constants.py` to fit your project name
```python
APP_NAME = "<your-project-name>"
```

### Image servers

Create a .ENV file for cantaloupe
```bash
sudo chmod +x <path/to>/cantaloupe/init.sh && cp <path/to>/cantaloupe/.env{.template,} && nano <path/to>/cantaloupe/.env
```

Modify the variables in order to fit your project (`BASE_URI` example: https://eida.obspm.fr)
```bash
BASE_URI=<url-used-for-prod-or-blank>
FILE_SYSTEM_SOURCE=./vhs-platform/mediafiles/img/
HTTP_PORT=8182
HTTPS_PORT=8183
LOG_PATH=/path/to/logs
```

Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
```shell
<path/to>/cantaloupe/init.sh
```

Create a service for cantaloupe
```bash
vi /etc/systemd/system/cantaloupe.service
```

```bash
[Unit]
Description=start cantaloupe
After=network.target
After=nginx.service

[Service]
WorkingDirectory=/<absolute/path/to>/vhs/
ExecStart=/<absolute/path/to>/vhs/cantaloupe/start.sh
StandardError=append:/<absolute/path/to>/vhs/cantaloupe/log

[Install]
WantedBy=multi-user.target
```

Launch SAS
```bash
cd sas && mvn jetty:run
```

### Gunicorn

Make sure you can serve app with Gunicorn then quit with Ctrl+C
```bash
gunicorn --bind 0.0.0.0:8000 vhs.wsgi
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
WorkingDirectory=<path/to>/vhs/vhs-platform
ExecStart=<path/to>/vhs/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          vhs.wsgi:application

[Install]
WantedBy=multi-user.target
```

The `/etc/nginx/sites-available/` directory should contain a config file for nginx named `vhs` for example:
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
        auth_basic              "Restricted Content";
        auth_basic_user_file    /etc/nginx/.htpasswd;
    }

    location /javax.faces.resource/ {
        proxy_pass http://0.0.0.0:8888/javax.faces.resource/;
    }

    location /static/ {
        autoindex off;
        alias </path/to>/vhs/vhs-platform/staticfiles;           # CHANGE HERE
    }

    location /media/ {
        autoindex off;
        alias </path/to>/vhs/vhs-platform/mediafiles/;           # CHANGE HERE
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

Reload the `systemd` manager configuration
```shell
sudo systemctl daemon-reload
```

- [Install VHS on Observatoire servers](https://syrte-int.obspm.fr/dokuwiki/wiki/informatique/prive/eida/installspe#cantaloupe_sas_et_vhs)

> (coming) Docker image

# Once the app is deployed...

## Code and files update
On update of the code, you will need to restart gunicorn
```shell
sudo systemctl restart gunicorn.socket
```

On modification of the static files, you will need to restart nginx
then copy static files into `vhs-platform/staticfiles` in order to be served but nginx
```shell
sudo systemctl restart nginx
./venv/bin/python vhs-platform/manage.py collectstatic
```

To make a command alias, copy that at the end of `~/.bashrc`:
```bash
alias djupdate="sudo systemctl restart gunicorn.socket && sudo systemctl restart nginx"
```

## Data model update
If the data model was changed, you will first need to check that the new data model do not cause any error in the application.
Once the tests performed, a migration file can be generated locally by running:
```shell
./venv/bin/python vhs-platform/manage.py makemigrations
```

It will create a file that tells Django how to modify the Postgres database structure to fit the new model definition.
To apply those modifications, run locally:
```shell
./venv/bin/python vhs-platform/manage.py migrate
```

If everything is set, update the remote database by running on the production server, once the code has been retrieve from origin:
```shell
./venv/bin/python vhs-platform/manage.py migrate
```

# Debug

Empty log file by running
```shell
sudo truncate -s 0 /path/to/logfile.log
```
To add aliases to your `.bashrc` config
```shell
vi ~/.bashrc       # paste aliases at the end
source ~/.bashrc   # to activate aliases
```

To activate DEBUG in prod in order to see Django errors (instead of 500 errors)
```shell
# install vhs/platform/requirements-dev.txt
vi vhs-platform/vhs/.env           # set DEBUG=True
vi vhs-platform/vhs/settings.py    # l.87 `if not DEBUG:` => `if DEBUG:`
```
Don't forget to rollback those modifications afterwards

## App errors
See `vhs-platform/logs`

```bash
alias djlog="cat vhs-platform/logs/<appname>.log"
alias empty_djlog="sudo truncate -s 0 vhs-platform/logs/<appname>.log"
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
