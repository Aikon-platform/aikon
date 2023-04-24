#!/bin/bash

# HOW TO USE
# Inside the scripts/ directory, run:
# sh prod_media.sh

scp -r eida:vhs/vhs-platform/mediafiles/* ../vhs-platform/mediafiles
