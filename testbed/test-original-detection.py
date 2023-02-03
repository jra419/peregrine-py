#!/usr/bin/env python3

from hosts.Tofino import Tofino
from hosts.Engine import Engine
from hosts.KitNet import KitNet
from hosts.TG_kernel import TG_kernel

import util
import json
import os
import shutil

SCRIPT_DIR       = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR = f'{SCRIPT_DIR}/results/original-rate-{SAMPLING_RATE}-sampling-rate'
VERBOSE          = False

DURATION_SECONDS = 300
SAMPLING_RATE    = 1024
# DURATION_SECONDS = 10
# SAMPLING_RATE    = 1

MAX_RETRIES      = 5

def check_success_from_controller_report(controller_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		ports_info = lines[1:]
		stats_port = int(ports_info[-1].split('\t')[0])

		rx_pkts    = 0
		tx_samples = 0

		for port_info in ports_info:
			port_info = port_info.split('\t')
			port      = int(port_info[0])
			rx        = int(port_info[1])
			tx        = int(port_info[2])

			if port != stats_port:
				rx_pkts += rx
			else:
				tx_samples = tx
				return rx_pkts > 0 and tx_samples > 0
		return False

def run(tofino, engine, kitnet, tg_kernel, testbed, test):
	print(f"[*] attack={test['attack']}")

	controller_report_file = None
	engine_report_file     = None

	success = False
	try_run = 0
	while not success:
		try_run += 1

		if try_run > MAX_RETRIES:
			print('Maximum number of allowed retries reached. Exiting.')
			exit(1)

		tofino.start()
		engine.start(testbed['engine']['listen-iface'])
		kitnet.start(
			test['models']['fm'],
			test['models']['el'],
			test['models']['ol'],
			test['models']['ts'],
		)

		tg_kernel.run(test['pcap'], testbed['tg']['tx-kernel-iface'], DURATION_SECONDS)

		tofino.stop()
		engine.stop()
		kitnet.stop()

		controller_report_file = tofino.get_report()
		engine_report_file     = engine.get_report()

		success = check_success_from_controller_report(controller_report_file)

		if not success:
			print(f"  - Packets not flowing through Tofino. Repeating experiment.")
	
	if not os.path.exists(TEST_RESULTS_DIR):
		os.makedirs(TEST_RESULTS_DIR)
	
	shutil.move(controller_report_file, f"{TEST_RESULTS_DIR}/{test['attack']}-controller.tsv")
	shutil.move(engine_report_file, f"{TEST_RESULTS_DIR}/{test['attack']}-engine.tsv")

if __name__ == '__main__':
	testbed = util.get_testbed_cfg()
	tests   = util.get_tests()

	tofino = Tofino(
		hostname=testbed['tofino']['hostname'],
		peregrine_path=testbed['tofino']['peregrine-path'],
		verbose=VERBOSE
	)
	
	engine = Engine(
		hostname=testbed['engine']['hostname'],
		peregrine_path=testbed['engine']['peregrine-path'],
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

	print('[*] Installing')
	tofino.modify_sampling_rate(SAMPLING_RATE)
	tofino.install()

	run(tofino, engine, kitnet, tg_kernel, testbed, target_test)