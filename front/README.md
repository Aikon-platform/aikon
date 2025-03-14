# <img alt="Aikon logo" src="app/webapp/static/favicon.ico" height="50" width="auto" style="display: inline; margin-bottom:-10px;"> AIKON

## Install 🛠️

### Requirements

- **Sudo** privileges
- **Bash** terminal
- **Python** >= 3.10
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

```bash
git clone git@github.com:Aikon-platform/aikon.git
cd aikon
```

### Scripted install 🐆

If you are using a Linux or Mac distribution, you can install the app with the following script:

```bash
bash scripts/setup.sh
```

Otherwise, follow the instructions below.

<details>
  <summary><h3>Manual install 🐢</h3></summary>

#### Dependencies
>
```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt-get install wget ca-certificates
sudo apt install python3-venv python3-dev libpq-dev nginx curl maven postgresql poppler-utils redis-server ghostscript
```
>
#### Python environment
>
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r app/requirements-dev.txt
```
>
Enable `pre-commit` hooks (auto-test and formatting)
>
```bash
pre-commit install
```
>
#### Project settings
>
Create a [Geonames](https://www.geonames.org/login) account and activate it.
>
Copy the content of the settings template file
```bash
cp app/config/.env{.template,}
```
Change variables in the generated file `app/config/.env` to corresponds to your database and username

Create a [Geonames](https://www.geonames.org/login) account, activate it and change `<geonames-username>` in the `.env` file
>
#### Database
>
Open Postgres command prompt, create a database (`<database>`) and a user
```bash
sudo -i -u postgres psql # Mac: psql postgres
postgres=# CREATE DATABASE <database>;
postgres=# CREATE USER <username> WITH PASSWORD '<password>';
postgres=# ALTER ROLE <username> SET client_encoding TO 'utf8';
postgres=# ALTER DATABASE <database> OWNER TO <username>;
postgres=# ALTER ROLE <username> SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE <username> SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE <database> TO <username>;
postgres=# \q
```
>
Update database schema with models that are stored inside `app/webapp/migrations`
```bash
python app/manage.py migrate
```
>
Create a superuser
```bash
python app/manage.py createsuperuser
```
>
#### Cantaloupe
>
Create a .ENV file for cantaloupe
```bash
sudo chmod +x cantaloupe/init.sh && cp cantaloupe/.env{.template,} && nano cantaloupe/.env
```
>
Change variables in the generated file `cantaloupe/.env`:
- `CANTALOUPE_BASE_URI`: leave it blank on local
- `CANTALOUPE_IMG` depends on the folder in which you run cantaloupe (inside cantaloupe/ folder: `../app/mediafiles/img/`)
```bash
CANTALOUPE_BASE_URI=
CANTALOUPE_IMG=absolute/path/to/app/mediafiles/img/  # inside the project directory
CANTALOUPE_PORT=8182
CANTALOUPE_PORT_HTTPS=8183
CANTALOUPE_DIR=/dir/where/cantaloupe/logs/will/be/stored
```
>
Set up Cantaloupe by running (it will create a `cantaloupe.properties` file with your variables):
```bash
bash cantaloupe/init.sh
```
>
Run [Cantaloupe](https://cantaloupe-project.github.io/)
```bash
bash cantaloupe/start.sh
```
>
#### Simple Annotation Server
>
Run [Simple Annotation Server](https://github.com/glenrobson/SimpleAnnotationServer)
```bash
cd sas && mvn jetty:run
```
>
Navigate to [http://localhost:8888/index.html](http://localhost:8888/index.html) to start annotating:
You should now see Mirador with default example manifests.
>
#### Enabling authentication for Redis instance (optional)
>
Get the redis config file and the redis password in the environment variables
```bash
REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
source app/config/.env
```
>
Add your `REDIS_PASSWORD` (from `app/config/.env`) to Redis config file
>
```bash
sudo sed -i -e "s/^requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
sudo sed -i -e "s/# requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
```
>
Restart Redis
```bash
sudo systemctl restart redis-server # Mac: brew services restart redis
```
>
Test the password
```
redis-cli -a $REDIS_PASSWORD
```
</details>

### Connection to API 📡

API code and instructions can be found in [this repository](https://github.com/Aikon-platform/discover-api).

[//]: # (TODO add instructions to setup api and front, locally or remotely)

## Launch app 🚀

Launch everything (Django, Celery, Cantaloupe and SimpleAnnotationServer) at once (stop with `Ctrl+C`):
```bash
bash run.sh
```

You can now visit the app at [http://localhost:8000](http://localhost:8000) and connect with the credentials you created

### *For more documentation, see [docs folder](docs/)*

## Project 📜

**[Aikon](https://aikon-platform.github.io/)** is a modular research platform designed to empower humanities scholars
in leveraging artificial intelligence and computer vision methods for analyzing large-scale heritage collections.
It offers a user-friendly interface for visualizing, extracting, and analyzing illustrations from historical documents,
fostering interdisciplinary collaboration and sustainability across digital humanities projects. Built on proven
technologies and interoperable formats, Aikon's adaptable architecture supports all projects involving visual materials.

***Aikon** is funded and supported by the Agence Nationale pour la Recherche and the European Research Council*
- **VHS** [ANR-21-CE38-0008](https://anr.fr/Projet-ANR-21-CE38-0008): computer Vision and Historical analysis of Scientific illustration circulation
- **EiDA** [ANR-22-CE38-0014](https://anr.fr/Projet-ANR-22-CE38-0014): EdIter et analyser les Diagrammes astronomiques historiques avec l’intelligence Artificielle
- **DISCOVER** project [ERC-101076028](https://cordis.europa.eu/project/id/101076028): Discovering and Analyzing Visual Structures

```bibtex
@misc{albouy2024aikon,
    title={AIKON: a computer vision platform for the Digital Humanities},
    author={
        Ségolène Albouy,
        Jade Norindr,
        Fouad Aouinti,
        Clara Grometto,
        Robin Champenois,
        Alexandre Guilbaud,
        Stavros Lazaris,
        Matthieu Husson,
        Mathieu Aubry
    },
    url={https://github.com/Aikon-platform/aikon},
    year={2024}
}
```
