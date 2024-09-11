# Final image
FROM ubuntu:22.04

ENV USER=aikon
ARG USERID

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
    python3-dev \
    python3-venv \
    supervisor \
    redis-server \
    nginx \
    maven \
    postgresql \
    ghostscript

# TODO make sure python 3.10 is installed
# TODO install java 11

WORKDIR /home/${USER}

# Copy app files
COPY --chown=${USER} ../app /home/${USER}/app
COPY --chown=${USER} ../cantaloupe /home/${USER}/cantaloupe
COPY --chown=${USER} ../celery /home/${USER}/celery
COPY --chown=${USER} ../gunicorn /home/${USER}/gunicorn
COPY --chown=${USER} ../sas /home/${USER}/sas
#COPY --chown=${USER} ../app/config/.env /home/${USER}/app/config/.env
COPY --chown=${USER} ./supervisord.conf /home/${USER}/supervisord.conf

# Install python dependencies
COPY --chown=${USER} ./requirements.txt /home/${USER}/app/requirements.txt
RUN python3.10 -m venv venv
RUN source venv/bin/activate && pip install --upgrade pip && pip install -r /home/${USER}/app/requirements.txt

## Initialize the database TODO make a docker compose for 2 container (app and db)
#COPY --chown=${USER} ../scripts/new_db.sh /home/${USER}/app/init_db.sh
#RUN chmod +x /home/${USER}/app/init_db.sh

# Create nginx config outside of the container
COPY docker/nginx.conf /etc/nginx/sites-available/aikon

# Must match the PORT in docker.sh
EXPOSE 8001 8182 8888

RUN mkdir -p /run && chown aikon:aikon /run

## Run command at each container launch
CMD export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf
