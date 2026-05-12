#!/bin/env bash

set -e

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ENVPATH="$SCRIPTPATH/.env"

if [ ! -f "$ENVPATH" ]; then
	echo "😿 $ENVPATH file not found. exiting...";
	exit 1;
fi

source "$ENVPATH"

echo ""
echo "🤔 copying files to remote server"
scp "$SCRIPTPATH/extract_pipeline_remote.sh" "$SCRIPTPATH/extract.sql" "$SCRIPTPATH/.env" "$SSH_CONNSTRING":"$FOLDER_WORK"

echo ""
echo "🤔 connecting to remote server and running extract_pipeline_remote.sh"
ssh -t "$SSH_CONNSTRING" "cd $FOLDER_WORK; bash ./extract_pipeline_remote.sh"

echo ""
echo "🤔 copying database extractions from remote server to local"
scp -r "$SSH_CONNSTRING:$FOLDER_WORK$FOLDER_OUT" .

echo ""
echo "🌞 done 🌞"
