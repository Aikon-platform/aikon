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
- **Geonames**:
    - Create an account on [Geonames](https://www.geonames.org/login) and activate it

## Installation

```bash
git clone git@github.com:faouinti/vhs.git
cd vhs
```

### Scripted install 🐆

If you are using a Linux or Mac distribution, you can install the app with the following script:

```bash
bash scripts/setup.sh
```

Otherwise, follow the instructions below.

<<<<<<< HEAD
### Repository

```bash
git clone git@github.com:faouinti/vhs.git
cd vhs
```

### Scripted install 🐆

If you are using a Linux or Mac distribution, you can install the app with the following script:

```bash
bash scripts/setup.sh
```

<<<<<<< HEAD
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

Copy the content of the settings template file
```bash
cp app/config/.env{.template,}
```

> #### Instructions done by the script
> Copy the content of the settings template file
=======
Otherwise, follow the instructions below.

> ### Manual install 🐢
> #### Dependencies
>>>>>>> eida-dev
>
> ```bash
> wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
> sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
> sudo apt update
> sudo apt-get install wget ca-certificates
> sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
> ```
>
> #### Python environment
>
> ```bash
> python3.10 -m venv venv
> source venv/bin/activate
> pip install -r app/requirements-dev.txt
> ```
>
> Enable `pre-commit` hooks (auto-test and formatting)
>
> ```bash
> pre-commit install
> ```
>
> #### Project settings
>
> Create a [Geonames](https://www.geonames.org/login) account and activate it.
>
> Copy the content of the settings template file
> ```bash
> cp app/config/.env{.template,}
> ```
> Change variables in the generated file `app/config/.env` to corresponds to your database and username
<<<<<<< HEAD
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
=======

>>>>>>> eida-dev
> Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file
>
> #### Database
>
<<<<<<< HEAD
> Provide as well an `APP_LANG`: only "fr" or "en" values are supported for now

Change variables in the generated file `app/config/.env` to corresponds to your database and username
Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file


### Database

Open Postgres command prompt, create a database (`<database>`) and a user
```bash
sudo -i -u postgres psql # psql postgres on a Mac
postgres=# CREATE DATABASE <database>;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
postgres=# ALTER DATABASE <database> OWNER TO <username>;
postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE <database> TO <username>;
postgres=# \q
```

### Django

Update database schema with models that are stored inside `app/webapp/migrations`
```bash
python app/manage.py migrate
```

Create a superuser
```shell
python app/manage.py createsuperuser
```

### IIIF Image server

#### Cantaloupe

Create a .ENV file for cantaloupe
```bash
sudo chmod +x cantaloupe/init.sh && cp cantaloupe/.env{.template,} && nano cantaloupe/.env
```

Change variables in the generated file `cantaloupe/.env`:
- `BASE_URI`: leave it blank on local
- `FILE_SYSTEM_SOURCE` depends on the folder in which you run cantaloupe (inside cantaloupe/ folder: `../app/mediafiles/img/`)
```bash
BASE_URI=
FILE_SYSTEM_SOURCE=absolute/path/to/app/mediafiles/img/  # inside the project directory
HTTP_PORT=8182
HTTPS_PORT=8183
LOG_PATH=/dir/where/cantaloupe/logs/will/be/stored
```

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

### Celery with Redis setup
#### Enabling authentication for Redis instance (optional)

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
=======
> ### Manual install 🐢
> #### Dependencies
>
> ```bash
> wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
> sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
> sudo apt update
> sudo apt-get install wget ca-certificates
> sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
> ```
>
> #### Python environment
>
> ```bash
> python3.10 -m venv venv
> source venv/bin/activate
> pip install -r app/requirements-dev.txt
> ```
>
> Enable `pre-commit` hooks (auto-test and formatting)
>
> ```bash
> pre-commit install
> ```
>
> #### Project settings
>
> Create a [Geonames](https://www.geonames.org/login) account and activate it.
>
> Copy the content of the settings template file
> ```bash
> cp app/config/.env{.template,}
> ```
> Change variables in the generated file `app/config/.env` to corresponds to your database and username
> Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file
>
> #### Database
>
=======
>>>>>>> eida-dev
> Open Postgres command prompt, create a database (`<database>`) and a user
> ```bash
> sudo -i -u postgres psql # Mac: psql postgres
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
> Update database schema with models that are stored inside `app/webapp/migrations`
> ```bash
> python app/manage.py migrate
> ```
>
> Create a superuser
> ```bash
> python app/manage.py createsuperuser
> ```
>
> #### Cantaloupe
>
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
> LOG_PATH=/dir/where/cantaloupe/logs/will/be/stored
> ```
>
> Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
> ```bash
> bash cantaloupe/init.sh
> ```
>
> Run [Cantaloupe](https://cantaloupe-project.github.io/)
> ```bash
> bash cantaloupe/start.sh
> ```
>
> #### Simple Annotation Server
>
> Run [Simple Annotation Server](https://github.com/glenrobson/SimpleAnnotationServer)
> ```bash
> cd sas && mvn jetty:run
> ```
>
> Navigate to [http://localhost:8888/index.html](http://localhost:8888/index.html) to start annotating:
> You should now see Mirador with default example manifests.
>
<<<<<<< HEAD
=======
> #### Svelte development
>
> Install Node.js and Webpack
> ```bash
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
> nvm install node
> npm install -g webpack webpack-cli
> ```
>
> Initialize npm in the webpack folder, and install all required packages:
> ```bash
> cd app/webpack
> npm init
> ```
>
> To compile the Svelte components, run:
> ```bash
> # in app/webpack
> npm run build
> ```
>
>>>>>>> eida-dev
> #### Enabling authentication for Redis instance (optional)
>
> Get the redis config file and the redis password in the environment variables
> ```bash
> REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
> source app/config/.env
> ```
>
> Add your `REDIS_PASSWORD` (from `app/config/.env`) to Redis config file
>
> ```bash
> sudo sed -i -e "s/^requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
> sudo sed -i -e "s/# requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
> ```
>
> Restart Redis
> ```bash
> sudo systemctl restart redis-server # Mac: brew services restart redis
> ```
>
> Test the password
> ```
> redis-cli -a $REDIS_PASSWORD
> ```
<<<<<<< HEAD
>>>>>>> ad0c783 ([DOCS] readme formatting)
=======
>>>>>>> eida-dev

## Launch app

Launch everything (Django, Celery, Cantaloupe and SimpleAnnotationServer) at once (stop with `Ctrl+C`):
```bash
bash run.sh
```

> Or launch each process separately:
> ```bash
> # Celery & Django
<<<<<<< HEAD
> venv/bin/celery -A app.app.celery worker -B -c 1 --loglevel=info -P threads && venv/bin/python app/manage.py runserver localhost:8000
=======
> venv/bin/celery -A app.config.celery worker -B -c 1 --loglevel=info -P threads && venv/bin/python app/manage.py runserver localhost:8000
>>>>>>> eida-dev
> # Cantaloupe
> sudo -S java -Dcantaloupe.config=cantaloupe/cantaloupe.properties -Xmx2g -jar cantaloupe/cantaloupe-4.1.11.war
> # Simple Annotation Server
> cd sas/ && mvn jetty:run
> ```

You can now visit the app at [http://localhost:8000](http://localhost:8000) and connect with the credentials you created

### *For more documentation, see [docs folder](docs/)*
