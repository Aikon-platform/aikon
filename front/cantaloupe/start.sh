#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
java -Dcantaloupe.config=$SCRIPT_DIR/cantaloupe.properties -Xmx2g -jar $SCRIPT_DIR/cantaloupe-4.1.11.war
