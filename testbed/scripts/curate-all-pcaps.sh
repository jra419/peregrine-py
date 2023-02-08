#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CURATE_SCRIPT="$SCRIPT_DIR/curate-pcap.py"

if [ $# -eq 0 ]; then
	echo "Usage: $0 <pcaps directory>"
	exit 1
fi

PCAPS_DIR="$(realpath $1)"

if [ ! -d $PCAPS_DIR ]; then
	echo "ERROR: $PCAPS_DIR not found."
	exit 1
fi

if ! ls $PCAPS_DIR | grep -E -q "\.(pcap|pcapng)$"; then
	echo "ERROR: No pcaps found in $PCAPS_DIR."
	exit 1
fi

cd $PCAPS_DIR
mkdir -p $PCAPS_DIR/curated

parallel \
	"echo 'Starting {}' && $CURATE_SCRIPT --input {} --output curated/{} >/dev/null && echo 'Done {}'" \
	::: *.pcap*