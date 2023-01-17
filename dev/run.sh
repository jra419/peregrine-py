#!/bin/bash

set -eou pipefail

SCRIPT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_DIR

SDE="bf-sde-9.7.0"
SDE_DIR="$SCRIPT_DIR/../$SDE"

setup() {
    # Creating shared folder
    rm -rf $SDE_DIR > /dev/null 2>&1
    mkdir -p $SDE_DIR

    # Building the container
    docker-compose build
}

# Check if shared directory doesn't exist or is empty
if [ ! -d $SDE_DIR ] || [ -z "$(ls -A $SDE_DIR)" ]; then
    setup
fi

docker-compose run --rm peregrine