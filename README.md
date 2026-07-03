# AIKON

<img src="https://aikon-platform.github.io/aikon-platform.png" alt="" height="500" width="auto">
Modular platform for the visual analysis of historical corpora, composed of a web application ([front/](front/README.md))
and a computer vision worker API ([api/](https://github.com/Aikon-platform/aikon-api/blob/main/README.md)). Both can be deployed together or separately.

## Requirements

- [Docker](https://docs.docker.com/engine/install/) with Compose v2
- [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/) (dev mode only)

## Install

```bash
git clone --recurse-submodules <repo-url> && cd aikon
python install.py
```

The installer asks for the install mode, generates every configuration file and starts the app:

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

If you find [this work](https://link.springer.com/article/10.1007/s10032-026-00581-x) useful, please consider citing:

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
    url={https://hal.science/hal-05248250},
    year={2025},
    month={Sep},
    number={hal-05248250},
    journal={HAL Pre-Print},
    keyword={Digital Humanities, Computer Vision, Historical Documents, Visual Analysis},
}
```
