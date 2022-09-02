#!/bin/bash

set -euo pipefail

VETH_SETUP="$SDE/install/bin/veth_setup.sh"
VETH_TEARDOWN="$SDE/install/bin/veth_teardown.sh"

RUN_TOFINO_MODEL="$SDE/run_tofino_model.sh"
RUN_SWITCHD="$SDE/run_switchd.sh"

# Trace file path.
TEST_PCAP=$1
# Trace file path for the execution phase.
TEST_PCAP_EXECUTION=$2
# Path to the trace file labels.
TRACE_LABELS_FILE=$3
# Sampling rate for the execution phase. Integer value (e.g., 8 means a sampling rate of 1/8).
SAMPLING_RATE=$4
# Define if the execution phase runs on the control/data plane (possible values: dp, cp).
EXEC_MODE=$5
# Name of the attack(s) present in the trace-file, used for generating the output files (e.g., dos-goldeneye).
ATTACK_NAME=$6

cleanup() {
	sudo $VETH_TEARDOWN > /dev/null 2>&1

	sudo pkill -f tofino-model
	sudo pkill -f tofino-model 2>/dev/null
	sudo pkill -f bf_switchd 2>/dev/null
	sudo pkill -f controller.py 2>/dev/null
	sudo pkill -f tcpreplay 2>/dev/null

	sudo rm -rf pcap_output
	sudo rm -f tmp.txt
	sudo rm -f *.log
	sudo rm -f zlog-cfg-cur
	sudo rm -rf pcap_output

	exit
}

trap cleanup EXIT

setup() {
	# Set up the virtual interfaces.
	echo "Setup veth."
	sudo $VETH_TEARDOWN > /dev/null 2>&1
	sudo $VETH_SETUP > /dev/null 2>&1

	# Start the tofino model.
	echo "Start tofino model."
	$RUN_TOFINO_MODEL --arch tofino -p ~/peregrine/p4/peregrine.p4 -c ~/peregrine/p4/multipipe_custom_bfrt.conf --int-port-loop 0xa -q > /dev/null 2>&1 &
	sleep 10

	# Start switchd.
	echo "Start switchd."
	$RUN_SWITCHD -p peregrine > /dev/null 2>&1 &
	sleep 10
}

run() {
	setup

	# Start the controller and training phase.
	echo "Start controller and training phase."
	sudo -E python3 -u ~/peregrine/py/controller.py --pcap $TEST_PCAP --labels $TRACE_LABELS_FILE --sampling $SAMPLING_RATE --execution $EXEC_MODE --attack $ATTACK_NAME >& tmp.txt &
	pid_controller=$!

	sleep 10

	if [[ "$EXEC_MODE" == "dp" ]]
	then
		sleep 1
		( tail -f -n0 tmp.txt & ) | grep -q "Starting execution phase..."

		sleep 5
		echo "Start the execution phase."
		sudo tcpreplay-edit --mtu-trunc -i "veth0" -x=0.25 $TEST_PCAP_EXECUTION
	fi

	wait $pid_controller
}

run
cleanup
