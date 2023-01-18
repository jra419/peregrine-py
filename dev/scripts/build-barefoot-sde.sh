#!/usr/bin/bash

set -euo pipefail

WORKSPACE=/home/docker

sudo apt-get update
sudo apt-get install python3 python3-pip cmake -y
sudo apt-get install libcli-dev -y

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1

pushd $WORKSPACE
    tar xvfz /opt/files/patches.tgz -C /opt/files
    tar xvfz /opt/files/bf-sde-9.7.0.tgz -C .
    tar xvfz /opt/files/ica-tools.tgz -C .

    patch -s -p0 < /opt/files/bf-sde-deps.patch

    pushd bf-sde-9.7.0
        echo "Y" | ./p4studio/p4studio dependencies install

        ./p4studio/p4studio configure thrift-diags '^tofino2' bfrt \
                            switch p4rt thrift-switch thrift-driver \
                            sai '^tofino2m' '^tofino2h' bf-diags cpuveth \
                            bfrt-generic-flags grpc tofino bsp \
                            --bsp-path=/opt/files/bf-reference-bsp-9.7.0.tgz

        ./p4studio/p4studio build
    popd

    patch -s -p0 < /opt/files/bf-sde-pkgsrc.patch
popd

echo "export SDE=$WORKSPACE/bf-sde-9.7.0" >> ~/.profile
echo "export SDE_INSTALL=$WORKSPACE/bf-sde-9.7.0/install" >> ~/.profile
echo "export PATH=$WORKSPACE/bf-sde-9.7.0/install/bin:\$PATH" >> ~/.zshrc
