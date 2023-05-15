# VHS platform

## Requirements

> - **Sudo** privileges
> - **Bash** terminal
> - **Python**: 3.10
> - **Java 11**: instructions for [Linux install](https://docs.oracle.com/en/java/javase/11/install/installation-jdk-linux-platforms.html#GUID-737A84E4-2EFF-4D38-8E60-3E29D1B884B8)
>     - [Download OpenJDK](https://jdk.java.net/11/) (open source version of Java)
>     - Download the latest [RPM Package](https://www.oracle.com/java/technologies/downloads/#java11)
>     - `sudo alien -i jdk-11.0.17_linux-aarch64_bin.rpm`
>     - `java -version` => `openjdk 11.x.x` // `java version "1.11.x"`
> - **Git**:
>     - `sudo apt install git`
>     - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

[//]: # (&#40;Mac: https://www.oracle.com/java/technologies/downloads/#java11-mac&#41;)

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

Mac
```bash
brew install wget ca-certificates postgresql maven nginx libpq poppler redis ghostscript
```

### Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r vhs-platform/requirements-dev.txt
```

Enable `pre-commit` hooks (auto-test and formatting)

```shell
pre-commit install
```

### Database

Open Postgres command prompt, create a database (`vhs`) and a user

[//]: # (createuser -s postgres)
[//]: # (psql -U postgres)

```bash
sudo -u postgres psql
postgres=# CREATE DATABASE vhs;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
postgres=# ALTER DATABASE vhs OWNER TO <username>;
postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE vhs TO <username>;
postgres=# \q
```

[//]: # (#### [pgAdmin]&#40;https://www.pgadmin.org&#41; &#40;GUI for PostgreSQL&#41;)
[//]: # ()
[//]: # (Provide email address and password. You should now access the interface )

### Project settings

Copy the content of the settings template file

```bash
cp vhs-platform/vhs/.env{.template,}
```

Change variables in the generated file `vhs-platform/vhs/.env` to corresponds to your database and username

```bash
ALLOWED_HOSTS="localhost,127.0.0.1,145.238.203.8"
SECRET_KEY="<secret-key>"            # random string of characters
DEBUG=True                           # leave to True on local
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
GEONAMES_USER="<geonames-username>"
APP_LANG="<fr-or-en>"                # lang to be used in the app: work either for french (fr) or english (en)
```

Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file

Add an `APP_NAME` and an `PROD_URL` with the scheme and domain used in production (e.g. "https://eida.obspm.fr")

Provide as well an `APP_LANG`: only "fr" or "en" values are supported for now

### Django

Update database schema with models that are stored inside `vhs-platform/vhsapp/migrations`
```bash
./venv/bin/python vhs-platform/manage.py migrate
```

Download static files to be stored in `vhs-platform/staticfiles`
```bash
./venv/bin/python vhs-platform/manage.py collectstatic
```

Create a super user
```shell
./venv/bin/python vhs-platform/manage.py createsuperuser
```

Create exception for port 8000
```shell
sudo ufw allow 8000
```

### IIIF Image server

#### Cantaloupe

Create a .ENV file for cantaloupe
```bash
sudo chmod +x cantaloupe/init.sh && cp cantaloupe/.env{.template,} && nano cantaloupe/.env
```

Change variables in the generated file `cantaloupe/.env`:
- `BASE_URI`: leave it blank on local
- `FILE_SYSTEM_SOURCE` on local: `../vhs-platform/mediafiles/img/` (double dots)
```bash
BASE_URI=
FILE_SYSTEM_SOURCE=./vhs-platform/mediafiles/img/
HTTP_PORT=8182
HTTPS_PORT=8183
LOG_PATH=/path/to/logs
```

Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
```shell
cantaloupe/init.sh
```

Run [Cantaloupe](https://cantaloupe-project.github.io/)
```shell
<path/to>/cantaloupe/start.sh
```

#### Simple Annotation Server
Run [Simple Annotation Server](https://github.com/glenrobson/SimpleAnnotationServer)
```shell
cd sas && mvn jetty:run
```

Navigate to [http://localhost:8888/index.html](http://localhost:8888/index.html) to start annotating:
You should now see Mirador with default example manifests.

## Launch app

Run server
```shell
./venv/bin/python vhs-platform/manage.py runserver localhost:8000
```

You can now visit the app at [http://localhost:8000](http://localhost:8000) and connect with the credentials you created

> For more documentation, see [docs folder](https://github.com/faouinti/vhs/tree/main/docs)
