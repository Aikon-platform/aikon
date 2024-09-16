# Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
ARG PORT

ENV USER=aikon

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
    libxext6 \
    libpq-dev \
    build-essential \
    poppler-utils \
    supervisor \
    maven \
    ghostscript \
    python3.10 \
    python3.10-venv \
    python3-pip

WORKDIR /home/${USER}

#COPY --chown=${USER} ../app /home/${USER}/app
#COPY --chown=${USER} ../gunicorn /home/${USER}/gunicorn
#COPY --chown=${USER} ../celery /home/${USER}/celery

# Copy app files
COPY --chown=${USER} app /home/${USER}/app
COPY --chown=${USER} gunicorn /home/${USER}/gunicorn
COPY --chown=${USER} celery /home/${USER}/celery
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

## TODO check if necessary if the have their own docker image
COPY --chown=${USER} cantaloupe /home/${USER}/cantaloupe
COPY --chown=${USER} sas /home/${USER}/sas

# Install python dependencies
COPY --chown=${USER} app/requirements-prod.txt /home/${USER}/app/requirements.txt
RUN python3.10 -m venv venv
RUN /home/${USER}/venv/bin/pip install --upgrade pip
RUN /home/${USER}/venv/bin/pip install -r /home/${USER}/app/requirements.txt

# Must match the PORT in docker.sh
EXPOSE ${PORT}

# For the gunicorn socket
RUN mkdir -p /run && chown ${USER}:${USER} /run

COPY --chown=${USER} docker/manage.sh /home/aikon/manage.sh
RUN chmod +x /home/aikon/manage.sh
COPY --chown=${USER} scripts/create_superuser.py /home/aikon/create_superuser.py

CMD ["/home/aikon/manage.sh"]

# Launch gunicorn
CMD export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf
