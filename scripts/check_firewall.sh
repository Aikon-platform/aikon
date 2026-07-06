#!/usr/bin/env bash

# for Linux distros, check for active firewalls. they may silently
# block connexions from the Docker subnet to the host, which is
# necessary for Docker containers to be able to interact with the
# Django app through HTTP. this script adds the Docker subnet to
# supported firewalls. useful for Debian, Ubuntu and Fedora.
#
# this should not be necessary on MacOS: macOS's Application Firewall (socketfilterfw)
# operates on application-level, not on IP/subnet/port-level. the
# `host.docker.internal` is managed by a single app (Docker), and MacOS
# does not block by default the container-to-host queries (as opposed to Linux).
#
# THIS ASSUMES the docker-compose is running.
#
# USAGE: bash check_firewall.sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER_DIR="$CUR_DIR"/../docker
ENV_FILE="$CUR_DIR/../front/app/config/.env"

source $ENV_FILE

# jq is a JSON parser in basj
if ! command -v jq &> /dev/null;
then sudo apt install jq;
fi;

# get docker network's subnet
# this can also be done through `docker compose` but requires the docker-compose
# and network to be active, and they are inactive in `install.py`.
# this alternative just parses the Docker-compose's config file/
cd "$DOCKER_DIR";
DOCKER_NETWORK=$(docker network ls \
  --filter label=com.docker.compose.project=aikon \
  --filter label=com.docker.compose.network=aikon \
  --format '{{.Name}}')
DOCKER_SUBNET=$(docker network inspect "$DOCKER_NETWORK" --format '{{(index .IPAM.Config 0).Subnet}}')

# 1. if we have an ufw firewall (enabled by default on Debian/Ubuntu)
# allow the Docker subnet in the firewall
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
  echo "Detected active ufw firewall — this commonly blocks Docker bridge traffic."
  echo "Allowing the subnet in ufw..."
  sudo ufw allow in from "$DOCKER_SUBNET" to any port "$FRONT_PORT"

# 2. if we have firewalld (Fedora),
# allow the Docker subnet in the firewall
elif command -v firewall-cmd &> /dev/null && sudo firewall-cmd --state 2>/dev/null | grep -q running; then
    echo "Detected active firewalld — may be blocking Docker bridge traffic."
    echo "Allowing the subnet in firewalld..."
    sudo firewall-cmd --permanent --zone=trusted --add-source="$DOCKER_SUBNET"
    sudo firewall-cmd --reload
fi
