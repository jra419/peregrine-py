#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cloc $SCRIPT_DIR/../controller --exclude-dir build,env,__pycache__ --exclude-ext=log,csv,tsv,txt,json,hpp

# https://stackoverflow.com/questions/47125660/counting-sum-of-lines-in-all-c-and-h-files
find $SCRIPT_DIR/../p4 -type f -name "*.p4" -print0 | \
	parallel -q0 -j0 --no-notice  wc -l {} | \
	awk '{ sum+=$1 }END{ print "P4 LoC: "sum }'