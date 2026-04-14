# 1st build: compile svelte files
FROM node:23 AS svelte_build

WORKDIR /app
COPY app .
WORKDIR /app/svelte/
RUN npm install --omit=dev
RUN npm run build

# ---------------------------------------
# 2nd build: Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
# probably useless
ARG PORT

ENV USER=aikon
ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_CACHE_DIR=/home/${USER}/.uv_cache
ENV UV_PROJECT_ENVIRONMENT=/home/${USER}/.venv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
ENV N_PROCESS=50

# Set up environment
ENV TERM=linux
SHELL ["/bin/bash", "-c"]
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#ENV http_proxy=http://195.221.193.15:3128
#ENV https_proxy=http://195.221.193.15:3128
#ENV no_proxy=localhost,127.0.0.1,.aikon_network
#ENV HTTP_PROXY=http://195.221.193.15:3128
#ENV HTTPS_PROXY=http://195.221.193.15:3128
#ENV NO_PROXY=localhost,127.0.0.1,.aikon_network

#RUN echo 'Acquire::http::Proxy "http://195.221.193.15:3128";' > /etc/apt/apt.conf.d/proxy.conf && \
#    echo 'Acquire::https::Proxy "http://195.221.193.15:3128";' >> /etc/apt/apt.conf.d/proxy.conf && \
#    echo 'Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/99disable-compressors && \
#    echo 'APT::Get::AllowUnauthenticated "true";' >> /etc/apt/apt.conf.d/99disable-compressors

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

WORKDIR /home/${USER}/app
# Install UV/python dependencies
RUN uv python install 3.11
RUN uv sync --locked --group=prod

# TODO less aggrssive permissions ?
# Set permissions on UV and NPM directories
# xargs is used to run chmod in parrallel in up to ${N_PROCESS} processes
RUN find ${UV_CACHE_DIR} -print0 | xargs -0 -P ${N_PROCESS} chown ${USER}:${USER}
# to speed up even more, we run the 3 chowns in parrallel and parrallelize each command using xargs
RUN \
    find ${UV_CACHE_DIR} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rwxXst & \
    find ${UV_PROJECT_ENVIRONMENT} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rX & \
    find ${UV_PYTHON_INSTALL_DIR} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rX & \
    wait

COPY --from=svelte_build --chown=${USER}:${USER} /app/webapp/static/svelte/* /home/${USER}/app/webapp/static/svelte/

WORKDIR /home/${USER}

EXPOSE 8000

# TODO set LC_ALL and LANG as Docker ENV vars ?
CMD /home/${USER}/manage.sh && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    # source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf

# NOTE currently, the app is owned by $USER but run by $ROOT.
# When installing, we
#   - creatin an aikon user account with a HOME directory
#   - put all necessary directories (incl. NPM and UV stuff) in the user's HOME,
#   - install everything in the HOME
#   - chmod everything so that the root user and the "aikon" user can access them
#   - run as a the app as Root
# NOTE a cleaner solution would be:
#   1. to install and run the app as $USER,
#   2. to install everything as ROOT and dipense of working ina user's home dir (less safe)
# with solution 1, python will be installed to /home/aikon/.local
# => no need to handle UV_PYTHON_INSTALL_DIR.
# >>> USER ${USER}
# >>> WORKDIR /home/${USER}/app
# >>> RUN uv python install 3.11
# >>> RUN uv sync --locked --group=prod

# NOTE: to debug, use these and see which parent directory doesn't have `x` (isn't executable).
# >>> ls -la /home/aikon/.venv/bin/python
# >>> namei -l /home/aikon/.venv/bin/python
