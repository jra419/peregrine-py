#!/usr/bin/bash

set -euo pipefail

SHARED="/shared"
SDE="/home/docker/bf-sde-9.7.0"

if [ -z "$(ls -A $SHARED)" ]; then
    # Shared folder is empty, so let's use copy all the boilerplate to the shared folder
    echo "Setting up shared folder, this might take a bit..."
    sudo cp -r $SDE/. $SHARED/
    sudo chown -R docker:docker $SHARED/
    echo "Done!"
fi

# Point the container to the shared folder
sudo rm -rf $SDE
sudo ln -s $SHARED $SDE
