# Final image
FROM ubuntu:22.04

# UPDATE THOSE VARIABLES
ENV USER=aikon
ARG USERID=$USERID
ARG PORT=$PORT

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
#    postgresql \
#    redis-server \
#    nginx \

WORKDIR /home/${USER}

## Copy app files
#COPY --chown=${USER} ../app /home/${USER}/app
#COPY --chown=${USER} ../gunicorn /home/${USER}/gunicorn
## TODO check if necessary if the have their own docker image
#COPY --chown=${USER} ../celery /home/${USER}/celery
#COPY --chown=${USER} ../cantaloupe /home/${USER}/cantaloupe
#COPY --chown=${USER} ../sas /home/${USER}/sas
#COPY --chown=${USER} ./supervisord.conf /home/${USER}/supervisord.conf
# Copy app files
COPY --chown=${USER} app /home/${USER}/app
COPY --chown=${USER} gunicorn /home/${USER}/gunicorn
## TODO check if necessary if the have their own docker image
COPY --chown=${USER} celery /home/${USER}/celery
COPY --chown=${USER} cantaloupe /home/${USER}/cantaloupe
COPY --chown=${USER} sas /home/${USER}/sas
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

# Install python dependencies
COPY --chown=${USER} app/requirements-prod.txt /home/${USER}/app/requirements.txt
RUN python3.10 -m venv venv
RUN /home/${USER}/venv/bin/pip install --upgrade pip
RUN /home/${USER}/venv/pip install -r /home/${USER}/app/requirements.txt

# Must match the PORT in docker.sh
EXPOSE ${PORT}

# For the gunicorn socket
RUN mkdir -p /run && chown ${USER}:${USER} /run

## Run command at each container launch
CMD export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf

COPY docker/manage.sh /home/aikon/manage.sh
RUN chmod +x /home/aikon/manage.sh

CMD ["/home/aikon/manage.sh"]
