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
CONFIGURATION_DIR="$SCRIPT_DIR/../confs/"
BFN_T10_032D_CONF_FILE="$CONFIGURATION_DIR/BFN-T10-032D-model.conf"

# If the tofino model is not running in the background, launch it
if ! ps -e | grep -q "$TOFINO_MODEL_EXE_NAME"; then
	echo "Tofino model not running. Exiting."
	exit 1
fi

# For some reason we need hugepages
if [ "$(grep HugePages_Total /proc/meminfo | awk '{print $2}')" = "0" ]; then \
	sudo sysctl -w vm.nr_hugepages=512 > /dev/null
fi

# Compile
make debug -j

# Run controller with model
echo "Running PEREGRINE_HW_CONF=$BFN_T10_032D_CONF_FILE sudo -E $CONTROLLER_EXE $TOPOLOGY_FILE --model"
PEREGRINE_HW_CONF=$BFN_T10_032D_CONF_FILE sudo -E $CONTROLLER_EXE $TOPOLOGY_FILE --model