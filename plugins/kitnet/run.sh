#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <models path> <attack>"
	exit 1
fi

MODELS_PATH=$(realpath $1)
ATTACK=$2

if ! test -d "$MODELS_PATH"; then
	echo "$MODELS_PATH not found."
	exit 1
fi

assert_file() {
	f=$1
	if ! test -f "$f"; then
		echo "$f not found."
		exit 1
	fi
}

KITNET_EXE="$SCRIPT_DIR/kitnet.py"

FM="$MODELS_PATH/m-10/$ATTACK-m-10-fm.txt"
EL="$MODELS_PATH/m-10/$ATTACK-m-10-el.txt"
OL="$MODELS_PATH/m-10/$ATTACK-m-10-ol.txt"
TS="$MODELS_PATH/m-10/$ATTACK-m-10-train-stats.txt"

assert_file $FM
assert_file $EL
assert_file $OL
assert_file $TS

$KITNET_EXE \
	--feature_map $FM \
	--ensemble_layer $EL \
	--output_layer $OL \
	--train_stats $TS