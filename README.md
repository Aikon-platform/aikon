# <img alt="Aikon logo" src="https://raw.githubusercontent.com/Aikon-platform/aikon/refs/heads/main/front/app/webapp/static/favicon.ico" height="50" width="auto" style="display: inline; margin-bottom:-10px;"> AIKON platform

[//]: # (<img src="https://media.springernature.com/full/springer-static/image/art%3A10.1007%2Fs10032-026-00581-x/MediaObjects/10032_2026_581_Fig1_HTML.png" alt="AIKON presentation" width="100%">)

Modular platform for the visual analysis of historical corpora, composed of a web application ([`front/`](front/README.md))
and a computer vision API ([`api/`](https://github.com/Aikon-platform/aikon-api/blob/main/README.md)).
Both can be deployed together or separately.

## Requirements

- [Python](https://www.python.org/downloads/) >= 3.10
- [Docker](https://docs.docker.com/engine/install/) with Compose v2
- `dev` mode only: [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/)

## Install

```bash
git clone --recurse-submodules git@github.com:Aikon-platform/aikon.git && cd aikon
python install.py
```

The script will ask you about the install mode, generate every configuration file and start the app:

| mode    | purpose       | what runs where                               |
|---------|---------------|-----------------------------------------------|
| `local` | use the app   | everything in Docker, no prompt, DEBUG on     |
| `dev`   | edit the code | services in Docker, front and api on the host |
| `prod`  | deploy        | everything in Docker, DEBUG off               |

## Run

```bash
python run.py         # start; in dev: Django + Celery + vite --watch, Ctrl+C to stop
python run.py down    # stop everything
python run.py logs    # follow the docker services logs
```

- `local`: app at `http://localhost:<NGINX_PORT>` (default 8080)
- `dev`: app at `http://localhost:<FRONT_PORT>` (default 8000); start the api separately with `python api/run.py`
- `prod`: served behind the host nginx at `https://<PROD_URL>` (SSL termination on the host, see [docker/nginx_external.conf.template](docker/nginx_external.conf.template))

## Configuration

The root [`.env`](.env.template) is the single source of truth: every other `.env` (front, cantaloupe, api, docker) is generated from it.
To change a value, edit the root `.env` then run:

```bash
python scripts/generate_env.py
```

Passwords and secret keys left blank are auto-generated. In `dev`/`local`, busy ports are automatically replaced by the next free one.

## Project

> [!NOTE]
> Historical document analysis has progressed to a point where the main bottleneck for many historical applications is
> not algorithms, but relevant interfaces, that can support historians’ workflow. While specialized tools exist for text
> processing and image search, we argue the community lacks a versatile collaborative platform enabling historians to
> analyze their own corpora from a particular perspective. As a step in this direction, we present **[Aikon](https://aikon-platform.github.io/)**, a modular
> web-platform designed to empower historians with computer vision tools. aikon implements a complete workflow for
> historical document analysis, from corpus constitution to ai outputs validation and interpretation. It provides a
> comprehensive research environment combining source management tools with automated processing capabilities as well
> as multi-user validation and visualization interfaces.

***Aikon** is funded and supported by the Agence Nationale pour la Recherche and the European Research Council*
- **VHS** [ANR-21-CE38-0008](https://anr.fr/Projet-ANR-21-CE38-0008): computer Vision and Historical analysis of Scientific illustration circulation
- **EiDA** [ANR-22-CE38-0014](https://anr.fr/Projet-ANR-22-CE38-0014): EdIter et analyser les Diagrammes astronomiques historiques avec l’intelligence Artificielle
- **DISCOVER** project [ERC-101076028](https://cordis.europa.eu/project/id/101076028): Discovering and Analyzing Visual Structures

If you find this work useful, please consider citing:

```bibtex
@article{albouy2026aikon,
    title={{AIKON : A Modular Computer Vision Platform for Historical Corpora}},
    author={
        Albouy, Ségolène and
        Norindr, Somkeo and
        Kervegan, Paul and
        Aouinti, Fouad and
        Delanaux, Rémy and
        Champenois, Robin and
        Grometto, Clara and
        Lazaris, Stavros and
        Guilbaud, Alexandre and
        Husson, Matthieu and
        Aubry, Mathieu
    },
    url={https://doi.org/10.1007/s10032-026-00581-x},
    year={2026},
    month={June},
    journal={International Journal on Document Analysis and Recognition (IJDAR)},
    keyword={Digital Humanities, Computer Vision, Historical Documents, Visual Analysis},
}
```
