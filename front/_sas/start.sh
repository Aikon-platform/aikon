#! /bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR" && mvn jetty:run -Djetty.port=${SAS_PORT:-8888}

# maybe no need to run this if this is added to docker-compose
# working_dir: /sas
# command: mvn jetty:run -Djetty.port=${SAS_PORT:-8888}
