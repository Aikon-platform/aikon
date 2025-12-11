# Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
# probably useless
ARG PORT

ENV USER=aikon
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/home/${USER}

RUN useradd -u ${USERID} -m -d /home/${USER} ${USER}

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
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql-client

WORKDIR /home/${USER}

COPY --chown=${USER} ./app/requirements-base.txt ./app/requirements-prod.txt ./

# Install python dependencies
RUN python3.10 -m venv venv && \
    /home/${USER}/venv/bin/pip install --upgrade pip && \
    /home/${USER}/venv/bin/pip install -r requirements-prod.txt

# Copy app files
COPY --chown=${USER} app /home/${USER}/app
COPY --chown=${USER} gunicorn /home/${USER}/gunicorn
COPY --chown=${USER} celery /home/${USER}/celery
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

RUN touch /home/${USER}/app/logs/app_log.log && chown ${USER}:${USER} /home/${USER}/app/logs/app_log.log
RUN touch /home/${USER}/app/logs/iiif.log && chown ${USER}:${USER} /home/${USER}/app/logs/iiif.log
RUN touch /home/${USER}/app/logs/download.log && chown ${USER}:${USER} /home/${USER}/app/logs/download.log

#EXPOSE ${PORT} # PORT is only used as outside port in docker-compose
EXPOSE 8000

RUN mkdir -p /home/${USER}/app/staticfiles && chown ${USER}:${USER} /home/${USER}/app/staticfiles

COPY --chown=${USER} docker/manage.sh /home/aikon/manage.sh
RUN chmod +x /home/aikon/manage.sh
RUN /home/${USER}/manage.sh

# Launch gunicorn
CMD export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    source venv/bin/activate && \
    supervisord -c /home/${USER}/supervisord.conf
