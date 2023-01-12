#!/usr/bin/bash

set -euo pipefail

WORKSPACE=/home/docker/

sudo apt update

# Ensure python 2 is not installed
if python2 -v; then
    echo "Python 2 found on the system. Removing."
    sudo apt remove -y python2 || true
    sudo apt autoremove -y || true
fi

sudo apt install python3 python3-pip lsb-core -y

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1

cd $WORKSPACE
git clone https://github.com/jafingerhut/p4-guide.git

cd p4-guide/bin/
./install-p4dev-v4.sh

echo "export BMV2=\"$WORKSPACE/p4-guide/bin/behavioral-model/\"" >> /home/docker/.zshrc
