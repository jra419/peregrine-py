#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

CONTROLLER_EXE="$SCRIPT_DIR/build/peregrine-controller"
VETH_SETUP_SCRIPT="$SCRIPT_DIR/../build_tools/veth_setup.sh"
TOFINO_MODEL_EXE_NAME="tofino-model"
TOPOLOGY_FILE="$SCRIPT_DIR/topology-model.json"

# If the tofino model is not running in the background, launch it
if ! ps -e | grep -q "$TOFINO_MODEL_EXE_NAME"; then
	echo "Tofino model not running. Exiting."
	exit 1
fi

# Compile
make debug -j

# Setup virtual ports
sudo $VETH_SETUP_SCRIPT

# Run controller with model
sudo -E $CONTROLLER_EXE $TOPOLOGY_FILE --model

# sudo tcpreplay -i veth0 -l 100 -L 1 ./uniform_100flows_64B.pcap
# sudo tcpdump -i veth2 -nv