# VHS platform

> ### *VHS is a research project funded and supported by the Agence Nationale pour la Recherche and the European Research Council*
> - **VHS** [ANR-21-CE38-0008](https://anr.fr/Projet-ANR-21-CE38-0008): computer Vision and Historical analysis of Scientific illustration circulation
> - **EiDA** [ANR-22-CE38-0014](https://anr.fr/Projet-ANR-22-CE38-0014): EdIter et analyser les Diagrammes astronomiques historiques avec l’intelligence Artificielle
> - **DISCOVER** project [ERC-101076028](https://cordis.europa.eu/project/id/101076028): Discovering and Analyzing Visual Structures

[//]: # (<img src="https://cdn-assets.inwink.com/e35f09cd-74e4-4383-8b70-15153fc0de48/9e39a716-4b31-408b-94f2-3af40901e6ac1">)
[//]: # (<img src="https://www.scattererid.eu/wp-content/uploads/2019/02/erc_logo.png">)

## Requirements

- **Sudo** privileges
- **Bash** terminal
- **Python**: 3.10
- **Java 11**: instructions for [Linux install](https://docs.oracle.com/en/java/javase/11/install/installation-jdk-linux-platforms.html#GUID-737A84E4-2EFF-4D38-8E60-3E29D1B884B8)
    - [Download OpenJDK](https://jdk.java.net/11/) (open source version of Java)
    - Download the latest [RPM Package](https://www.oracle.com/java/technologies/downloads/#java11)
    - `sudo alien -i jdk-11.0.17_linux-aarch64_bin.rpm`
    - `java -version` => `openjdk 11.x.x` // `java version "1.11.x"`
- **Git**:
    - `sudo apt install git`
    - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

[//]: # (https://www.oracle.com/java/technologies/javase/jdk11-archive-downloads.html)

## App set up

### Repository

```bash
git clone git@github.com:faouinti/vhs.git
cd vhs
```

### Dependencies

```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt-get install wget ca-certificates
sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
```

[//]: # (Mac OS)
[//]: # (```bash)
[//]: # (brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript)
[//]: # (brew services start postgresql)
[//]: # (brew services start redis)
[//]: # (```)

### Python environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r app/requirements-dev.txt
```

Enable `pre-commit` hooks (auto-test and formatting)

```shell
pre-commit install
```

### Project settings

Create a [Geonames](https://www.geonames.org/login) account and activate it.

Fill the various `.env` files of the project with:
```shell
bash scripts/env.sh
```

> #### Instructions done by the script
> Copy the content of the settings template file
>
> ```bash
> cp app/config/.env{.template,}
> ```
>
> Change variables in the generated file `app/config/.env` to corresponds to your database and username
>
> ```bash
> APP_NAME="Lower case name of the application"
> CONTACT_MAIL="Email address for support and inquiries"
> DB_NAME="Database name"
> DB_USERNAME="Database admin name"
> DB_PASSWORD="Database password"
> ALLOWED_HOSTS="List of allowed host separated by a comma"
> SECRET_KEY="Random string of characters"
> DEBUG="True or False"
> DB_HOST="Database host"
> DB_PORT="Database port"
> SAS_USERNAME="SimpleAnnotationServer username"
> SAS_PASSWORD="SimpleAnnotationServer password"
> SAS_PORT="SimpleAnnotationServer port"
> CANTALOUPE_PORT="Cantaloupe port"
> CANTALOUPE_PORT_HTTPS="Cantaloupe port used on production"
> PROD_URL="URL used in production without 'https://'"
> GEONAMES_USER="Geonames username"
> APP_LANG="fr or en"
> EXAPI_URL="API URL to which send requests for image analysis"
> EXAPI_KEY="API secret key to allow requests for image analysis"
> EXTRACTOR_MODEL="Pre-trained model used for image analysis"
> REDIS_PASSWORD="Redis password"
> MEDIA_DIR="Absolute path to media files directory"
> EMAIL_HOST="SMTP server domain"
> EMAIL_HOST_USER="Email address to send alert emails"
> EMAIL_HOST_PASSWORD="App password for email address"
> ```
>
> Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file
>
> Add an `APP_NAME` and an `PROD_URL` with the scheme and domain used in production (e.g. "eida.obspm.fr")
>
> Provide as well an `APP_LANG`: only "fr" or "en" values are supported for now

### Database

In a terminal inside the `scripts/` directory, run:

```shell
bash new_db.sh <database-name>
```

You will be asked to type your sudo password, then the password for the Django superuser (same name as `$DB_USERNAME`) twice.

> #### Instructions done by the script
> Open Postgres command prompt, create a database (`<database>`) and a user
>
> [//]: # (psql postgres)
>
> ```bash
> sudo -i -u postgres psql
> postgres=# CREATE DATABASE <database>;
> postgres=# CREATE USER <username> WITH PASSWORD '<password>';
> postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
> postgres=# ALTER DATABASE <database> OWNER TO <username>;
> postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
> postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
> postgres=# GRANT ALL PRIVILEGES ON DATABASE <database> TO <username>;
> postgres=# \q
> ```
>
> ### Django
>
> Update database schema with models that are stored inside `app/webapp/migrations`
> ```bash
> python app/manage.py migrate
> ```
>
> Create a superuser
> ```shell
> python app/manage.py createsuperuser
> ```

Create exception for port 8000
```shell
sudo ufw allow 8000
```

### IIIF Image server

#### Cantaloupe

Skip these steps if you used `scripts/env.sh`

> Create a .ENV file for cantaloupe
> ```bash
> sudo chmod +x cantaloupe/init.sh && cp cantaloupe/.env{.template,} && nano cantaloupe/.env
> ```
>
> Change variables in the generated file `cantaloupe/.env`:
> - `BASE_URI`: leave it blank on local
> - `FILE_SYSTEM_SOURCE` depends on the folder in which you run cantaloupe (inside cantaloupe/ folder: `../app/mediafiles/img/`)
> ```bash
> BASE_URI=
> FILE_SYSTEM_SOURCE=absolute/path/to/app/mediafiles/img/  # inside the project directory
> HTTP_PORT=8182
> HTTPS_PORT=8183
> LOG_PATH=/dir/where/cantaloupe/logs/are/stored
> ```

Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
```shell
bash cantaloupe/init.sh
```

Run [Cantaloupe](https://cantaloupe-project.github.io/)
```shell
bash cantaloupe/start.sh
```

#### Simple Annotation Server
Run [Simple Annotation Server](https://github.com/glenrobson/SimpleAnnotationServer)
```shell
cd sas && mvn jetty:run
```

Navigate to [http://localhost:8888/index.html](http://localhost:8888/index.html) to start annotating:
You should now see Mirador with default example manifests.

The Simple Annotation Server project does not currently contain authentication although it is possible to secure the SAS web application with a single username and password using Nginx forwarding.

Create the password file using the OpenSSL utilities and add a username to the file
```bash
sudo sh -c "echo -n '<username>:' >> /etc/nginx/.htpasswd"
```

Next, add an encrypted password entry for the username
```bash
sudo sh -c "openssl passwd <password> >> /etc/nginx/.htpasswd"
```

You can repeat this process for additional usernames.

To configure Nginx password authentication, open up the server block configuration file and set up authentication
```bash
sudo vi /etc/nginx/sites-enabled/vhs
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

### Celery with Redis setup
#### Enabling authentication for Redis instance

Get the redis config file and the redis password in the environment variables
```bash
REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
source app/config/.env
```

Add your `REDIS_PASSWORD` (from `app/config/.env`) to Redis config file

```bash
sudo sed -i -e "s/^requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
sudo sed -i -e "s/# requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
```

Restart Redis
```bash
sudo systemctl restart redis-server # brew services restart redis
```

Test the password
```
redis-cli -a $REDIS_PASSWORD
```

## Launch app

Run server
```shell
venv/bin/celery -A app.app.celery worker -B -c 1 --loglevel=info -P threads && venv/bin/python app/manage.py runserver localhost:8000
```

or to launch everything (Django, Cantaloupe and SimpleAnnotationServer) at once (stop with `kill 0`):
```shell
bash run.sh
```

You can now visit the app at [http://localhost:8000](http://localhost:8000) and connect with the credentials you created

> For more documentation, see [docs folder](https://github.com/faouinti/vhs/tree/main/docs)
