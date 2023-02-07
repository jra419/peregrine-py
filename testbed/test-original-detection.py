#!/usr/bin/env python3

from hosts.Tofino import Tofino
from hosts.Dispatcher import Dispatcher
from hosts.KitNet import KitNet
from hosts.TG_kernel import TG_kernel

import util
import json
import os
import shutil

# DURATION_SECONDS = 300
# SAMPLING_RATE    = 1024
DURATION_SECONDS = 10
SAMPLING_RATE    = 1

SCRIPT_DIR       = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR = f'{SCRIPT_DIR}/results/original-rate-{SAMPLING_RATE}-sampling-rate'
VERBOSE          = False

def check_success_from_controller_report(controller_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		ports_info = lines[1:]
		stats_port = int(ports_info[-1].split('\t')[0])

		total_rx_bytes   = 0
		total_rx_pkts    = 0
		total_tx_samples = 0

		for port_info in ports_info:
			port_info = port_info.split('\t')
			port      = int(port_info[0])
			rx_bytes  = int(port_info[1])
			rx_pkts   = int(port_info[2])
			tx_bytes  = int(port_info[3])
			tx_pkts   = int(port_info[4])

			if port != stats_port:
				total_rx_bytes += rx_bytes
				total_rx_pkts  += rx_pkts
			else:
				total_tx_samples = tx_pkts
				return total_rx_pkts > 0 and total_tx_samples > 0
		return False

def run(tofino, dispatcher, kitnet, tg_kernel, testbed, test):
	print(f"[*] attack={test['attack']}")

	controller_report_file = None
	dispatcher_report_file = None

	success = False
	while not success:
		tofino.start()
		dispatcher.start(testbed['dispatcher']['listen-iface'])
		kitnet.start(
			test['models']['fm'],
			test['models']['el'],
			test['models']['ol'],
			test['models']['ts'],
		)

		tg_kernel.run(test['pcap'], testbed['tg']['tx-kernel-iface'], DURATION_SECONDS)

		tofino.stop()
		dispatcher.stop()
		kitnet.stop()

		controller_report_file = tofino.get_report()
		dispatcher_report_file = dispatcher.get_report()

		success = check_success_from_controller_report(controller_report_file)

		if not success:
			print(f"  - Packets not flowing through Tofino. Repeating experiment.")
	
	if not os.path.exists(TEST_RESULTS_DIR):
		os.makedirs(TEST_RESULTS_DIR)
	
	shutil.move(controller_report_file, f"{TEST_RESULTS_DIR}/{test['attack']}-controller.tsv")
	shutil.move(dispatcher_report_file, f"{TEST_RESULTS_DIR}/{test['attack']}-dispatcher.tsv")

if __name__ == '__main__':
	testbed = util.get_testbed_cfg()
	tests   = util.get_tests()

	tofino = Tofino(
		hostname=testbed['tofino']['hostname'],
		peregrine_path=testbed['tofino']['peregrine-path'],
		verbose=VERBOSE
	)
	
	dispatcher = Dispatcher(
		hostname=testbed['dispatcher']['hostname'],
		peregrine_path=testbed['dispatcher']['peregrine-path'],
		verbose=VERBOSE
	)

	kitnet = KitNet(
		hostname=testbed['plugins']['kitnet']['hostname'],
		peregrine_path=testbed['plugins']['kitnet']['peregrine-path'],
		verbose=VERBOSE
	)

	tg_kernel = TG_kernel(
		hostname=testbed['tg']['hostname'],
		verbose=VERBOSE
	)

	target_test = None

	for test in tests['tests']:
		if test['attack'] == 'os-scan':
			target_test = test

	assert target_test

	# print('[*] Installing')
	# tofino.modify_sampling_rate(SAMPLING_RATE)
	# tofino.install()

	run(tofino, dispatcher, kitnet, tg_kernel, testbed, target_test)