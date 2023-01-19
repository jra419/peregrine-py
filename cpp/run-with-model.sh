#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

if [ -z ${SDE_INSTALL+x} ]; then
	echo "SDE_INSTALL env var not set. Exiting."
	exit 1
fi

CONTROLLER_EXE="$SCRIPT_DIR/build/peregrine-controller"
TOPOLOGY_FILE="$SCRIPT_DIR/topology-model.json"
TOFINO_MODEL_EXE_NAME="tofino-model"
BFN_T10_032D_CONF_FILE="$SCRIPT_DIR/../confs/BFN-T10-032D.conf"

# If the tofino model is not running in the background, launch it
if ! ps -e | grep -q "$TOFINO_MODEL_EXE_NAME"; then
	echo "Tofino model not running. Exiting."
	exit 1
fi

# Compile
make debug -j

# Run controller with model
PEREGRINE_HW_CONF=$BFN_T10_032D_CONF_FILE sudo -E $CONTROLLER_EXE $TOPOLOGY_FILE --model