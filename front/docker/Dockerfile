# Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
# probably useless
ARG PORT

ENV USER=aikon
# PYTHONUNBUFFERED still works with UV
ENV PYTHONUNBUFFERED=1

# ENV PYTHONPATH=/home/${USER}
# disable UV dev dependencies
ENV UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1

RUN useradd -u ${USERID} -m -d /home/${USER} ${USER}

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
    # python3.10 \
    # python3.10-venv \
    # python3-pip \
    postgresql-client \
    libcairo2-dev

# install UV. https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /home/${USER}

COPY --chown=${USER} ./app/requirements-base.txt ./app/requirements-prod.txt ./

# Install python dependencies
# RUN python3.10 -m venv venv && \
#     /home/${USER}/venv/bin/pip install --upgrade pip && \
#     /home/${USER}/venv/bin/pip install -r requirements-prod.txt

# Copy app files
COPY --chown=${USER} app /home/${USER}/app
COPY --chown=${USER} gunicorn /home/${USER}/gunicorn
COPY --chown=${USER} celery /home/${USER}/celery
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

# Install UV/python dependencies
RUN uv python install 3.11
RUN uv --directory=/home/${USER}/app sync

RUN touch /home/${USER}/app/logs/app_log.log && chown ${USER}:${USER} /home/${USER}/app/logs/app_log.log
RUN touch /home/${USER}/app/logs/iiif.log && chown ${USER}:${USER} /home/${USER}/app/logs/iiif.log
RUN touch /home/${USER}/app/logs/download.log && chown ${USER}:${USER} /home/${USER}/app/logs/download.log

#EXPOSE ${PORT} # PORT is only used as outside port in docker-compose
EXPOSE 8000

RUN mkdir -p /home/${USER}/app/staticfiles && chown ${USER}:${USER} /home/${USER}/app/staticfiles

COPY --chown=${USER} docker/manage.sh /home/aikon/manage.sh
RUN chmod +x /home/${USER}/manage.sh

# ultra bourrin: chown the .venv used by UV.
# NOTE : this *might* be useful: https://stackoverflow.com/questions/79787507/changing-the-owner-of-venv-created-by-uv-inside-docker/79788084#comment140788993_79787507
# TODO : plein d'erreurs de permission avec UV
RUN chown -R ${USER} /home/${USER}/app/
# UV writes cache in /root
RUN chmod +x ${USER} /root/.cache

# Launch gunicorn
CMD /home/${USER}/manage.sh && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    # source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf
