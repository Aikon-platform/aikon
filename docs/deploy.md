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

Change variables in the generated file `vhs-platform/vhs/.env` to corresponds to your database and username
```bash
ALLOWED_HOSTS="localhost,127.0.0.1,<project-host-name>"
SECRET_KEY="<secret-key>" # random string of characters
DEBUG=False
DB_NAME="<database-name>"
DB_USERNAME="<database-username>"
DB_PASSWORD="<database-password>"
DB_HOST="<database-host>"
DB_PORT="<database-port>"
SAS_USERNAME="<sas-username>"
SAS_PASSWORD="<sas-password>"
GPU_REMOTE_HOST="<gpu-host>"
GPU_USERNAME="<gpu-username>"
GPU_PASSWORD="<gpu-password>"
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

Change the following parameters in `cantaloupe.properties`:
```yaml
http.port = 8182
...
https.port = 8183
...
base_uri = http://<project-domaine-name>
```

Run Cantaloupe
```bash
sudo java -Dcantaloupe.config=cantaloupe/cantaloupe.properties -Xmx2g -jar cantaloupe/cantaloupe*.war
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

- [Install VHS on Observatoire servers](https://syrte-int.obspm.fr/dokuwiki/wiki/informatique/prive/eida/installspe#cantaloupe_sas_et_vhs)

> (coming) Docker image

# Once the app is deployed...

On update of the code, you will need to restart gunicorn
```shell
sudo systemctl restart gunicorn
```

On modification of the static files, you will need to restart nginx
```shell
sudo systemctl restart nginx
```
