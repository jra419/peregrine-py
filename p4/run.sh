#!/bin/sh

cd ~/bf-sde-9.5.0/p4-build-9.5.0/
make clean
./configure --prefix=$SDE_INSTALL --with-p4c --with-tofino --enable-thrift P4_NAME=kitsune P4_PATH=~/Documents/TEMP/kitsune-recirculation/kitsune.p4 P4_VERSION=p4-16 P4_ARCHITECTURE=tna
make
make install

