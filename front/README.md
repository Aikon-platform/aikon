# AIKON front

Django + Svelte web application: document management, image annotation (aiiinotate + Mirador),
IIIF image serving (Cantaloupe), asynchronous tasks (Celery + Redis).

## Development

From the repository root:

```bash
python install.py --mode dev
python run.py
```

`run.py` starts on the host: Django (`runserver`), the Celery worker and beat, and `vite build --watch` (Svelte components are recompiled on save).
PostgreSQL, Redis, MongoDB, Cantaloupe, aiiinotate and Mirador run as Docker services defined in [docker/compose.yml](../docker/compose.yml).
`Ctrl+C` stops the host processes; the services keep running (`python run.py down` stops them too).

Common tasks, from `front/app`:

```bash
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py shell
```

Database utilities (dump, restore, reset) are in [scripts/](scripts/).

## Svelte

Components live in [app/svelte](app/svelte) and are compiled to `app/webapp/static/svelte`, identically in every mode.

To build manually:
```bash
cd app/svelte && npm run build
```

## Configuration

[app/config/.env](app/config/.env) is generated from the root `.env`;
do not edit it directly (see the [root README](../README.md#configuration)).
Settings are split between [base.py](app/config/settings/base.py),
[dev.py](app/config/settings/dev.py) (used by the `local` and `dev` modes)
and [prod.py](app/config/settings/prod.py), selected by the `MODE` variable.

## Deployment

The front is deployed with the rest of the stack (`python install.py --mode prod` from the root).
Its image is built from [docker/Dockerfile](docker/Dockerfile): a node stage compiles the Svelte components,
then gunicorn and Celery run under supervisord ([docker/supervisord.conf](docker/supervisord.conf));
migrations and `collectstatic` run at container startup ([docker/manage.sh](docker/manage.sh)).

## Citation

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
