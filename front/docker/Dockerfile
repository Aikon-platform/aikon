# Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
# probably useless
ARG PORT

ENV USER=aikon
# PYTHONUNBUFFERED still works with UV
ENV PYTHONUNBUFFERED=1

ENV UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_CACHE_DIR=/home/${USER}/.uv_cache
ENV UV_PROJECT_ENVIRONMENT=/home/${USER}/.venv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python

# Set up environment
ENV TERM=linux
SHELL ["/bin/bash", "-c"]
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    zip \
    curl \
    ca-certificates \
    ffmpeg \
    libsm6 \
    libmagic1 \
    libxext6 \
    libpq-dev \
    build-essential \
    poppler-utils \
    supervisor \
    ghostscript \
    postgresql-client \
    libcairo2-dev

# install UV. https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd -u ${USERID} -m -d /home/${USER} ${USER}

WORKDIR /home/${USER}

# Copy app files
COPY --chown=${USER} app /home/${USER}/app
COPY --chown=${USER} gunicorn /home/${USER}/gunicorn
COPY --chown=${USER} celery /home/${USER}/celery
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

RUN touch /home/${USER}/app/logs/app_log.log && chown ${USER}:${USER} /home/${USER}/app/logs/app_log.log
RUN touch /home/${USER}/app/logs/iiif.log && chown ${USER}:${USER} /home/${USER}/app/logs/iiif.log
RUN touch /home/${USER}/app/logs/download.log && chown ${USER}:${USER} /home/${USER}/app/logs/download.log

RUN mkdir -p /home/${USER}/app/staticfiles && chown ${USER}:${USER} /home/${USER}/app/staticfiles

COPY --chown=${USER}:${USER} docker/manage.sh /home/aikon/manage.sh
RUN chmod +x /home/${USER}/manage.sh

# Install UV/python dependencies and set permissions
WORKDIR /home/${USER}/app
RUN uv python install 3.11
RUN uv sync --locked --group=prod
RUN chown -R ${USER}:${USER} ${UV_CACHE_DIR}
# TODO less aggrssive permissions ?
# all on cache
RUN chmod a+rwxXst -R ${UV_CACHE_DIR}
# read + execute on the environment
RUN chmod -R a+rX ${UV_PROJECT_ENVIRONMENT}
# read + execute on the python install dir to which the .venv will symlink
RUN chmod -R a+rX ${UV_PYTHON_INSTALL_DIR}

# NOTE: the problem was a permissions issue on the venv:
# without UV_PYTHON_INSTALL_DIR, uv installs python in the repo
# of the user installing python => in our case, /root/.local
# so, the python in .venv is a symlink to /root/.local, for
# which we don't have an execution permissions.
# OUR FIX: the solution is
# - set UV_PYTHON_INSTALL_DIR
# - set UV_PROJECT_ENVIRONMENT and UV_CACHE in /home/aikon
# - set rX on UV_PROJECT_ENVIRONMENT so that python can execute the python

# NOTE a cleaner solution would be to install and run the app as $USER,
# instead of the app being owned by $USER but run by $ROOT:
# them python will be installed to /home/aikon/.local
# => no need to handle UV_PYTHON_INSTALL_DIR.
# >>> USER ${USER}
# >>> WORKDIR /home/${USER}/app
# >>> RUN uv python install 3.11
# >>> RUN uv sync --locked --group=prod

# NOTE: to debug, use these and see which parent directory doesn't have `x` (isn't executable).
# >>> ls -la /home/aikon/.venv/bin/python
# >>> namei -l /home/aikon/.venv/bin/python


WORKDIR /home/${USER}

EXPOSE 8000

# TODO set LC_ALL and LANG as Docker ENV vars ?
CMD /home/${USER}/manage.sh && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    # source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf
