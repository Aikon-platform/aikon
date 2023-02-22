# VHS platform

## Requirements

> - **Sudo** privileges
> - **Python**: 3.10
> - **Java 11**: instructions for [Linux install](https://docs.oracle.com/en/java/javase/11/install/installation-jdk-linux-platforms.html#GUID-737A84E4-2EFF-4D38-8E60-3E29D1B884B8)
>     - [Download OpenJDK](https://jdk.java.net/11/) (open source version of Java)
>     - Download the latest [RPM Package](https://www.oracle.com/java/technologies/downloads/#java11)
>     - `sudo alien -i jdk-11.0.17_linux-aarch64_bin.rpm`
>     - `java -version` => `openjdk 11.x.x` // `java version "1.11.x"`
> - **Git**:
>     - `sudo apt install git`
>     - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

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
sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql
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

```bash
sudo -u postgres psql
postgres=# CREATE DATABASE vhs;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
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
ALLOWED_HOSTS="localhost,127.0.0.1"
SECRET_KEY="<secret-key>"
DEBUG=True
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

### Launching the app

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

Launch server
```shell
./venv/bin/python vhs-platform/manage.py runserver localhost:8000
```

You can now visit the app at [http://localhost:8000](http://localhost:8000) and connect with the credentials you just created

## IIIF

### IIIF Image server

#### Cantaloupe
Run [Cantaloupe](https://cantaloupe-project.github.io/)
```shell
# Unix distributions
sudo java -Dcantaloupe.config=cantaloupe/cantaloupe.properties -Xmx2g -jar cantaloupe/cantaloupe*.war

# Windows
java -Dcantaloupe.config=C:cantaloupe/cantaloupe.properties -Xmx2g -jar cantaloupe/cantaloupe*.war
```

[//]: # (If `Exception in thread "main" java.io.IOException: Failed to bind to /0.0.0.0:80`)
[//]: # (`Caused by: java.net.BindException: Address already in use`)
[//]: # (```shell)
[//]: # (sudo lsof -i :80)
[//]: # (sudo kill <pid1> <pid2> ...)
[//]: # (```)

#### Simple Annotation Server
Run [Simple Annotation Server](https://github.com/glenrobson/SimpleAnnotationServer)
```shell
cd sas && mvn jetty:run
```

Navigate to [http://localhost:8888/index.html](http://localhost:8888/index.html) to start annotating:
You should now see Mirador with default example manifests.

> For more documentation, see [docs folder](https://github.com/faouinti/vhs/tree/main/docs)
