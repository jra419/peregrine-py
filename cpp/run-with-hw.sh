#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

if [ -z ${SDE_INSTALL+x} ]; then
	echo "SDE_INSTALL env var not set. Exiting."
	exit 1
fi

CONTROLLER_EXE="$SCRIPT_DIR/build/peregrine-controller"
TOPOLOGY_FILE="$SCRIPT_DIR/topology.json"

LD_LIBRARY_PATH="/usr/local/lib/:$SDE_INSTALL/lib/"
BFN_T10_032D_CONF_FILE="$SCRIPT_DIR/../confs/BFN-T10-032D.conf"

# Compile
make release -j

# Run controller with model
LD_LIBRARY_PATH=$LD_LIBRARY_PATH PEREGRINE_HW_CONF=$BFN_T10_032D_CONF_FILE $CONTROLLER_EXE $TOPOLOGY_FILE