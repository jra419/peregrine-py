#!/usr/bin/env python3

from hosts.Tofino import Tofino
from hosts.Engine import Engine
from hosts.KitNet import KitNet
from hosts.TG_DPDK import TG_DPDK

import util

import hosts
import os

SCRIPT_DIR        = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR  = f'{SCRIPT_DIR}/results/sampling-rate'
VERBOSE           = False

MIN_SAMPLING_RATE = 1024
# MAX_SAMPLING_RATE = 16384
MAX_SAMPLING_RATE = 2048

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

	tg_dpdk = TG_DPDK(
		hostname=testbed['tg']['hostname'],
		verbose=VERBOSE
	)

	sampling_rate = MIN_SAMPLING_RATE
	results = {}

	while sampling_rate <= MAX_SAMPLING_RATE:
		print(f'[*] Installing...')
		tofino.modify_sampling_rate(sampling_rate)
		tofino.install()

		n_tests = 0
		for test in tests['tests']:
			if n_tests >= 2:
				break
			n_tests += 1

			attack = test['attack']
			print(f"[*] attack={attack} sampling_rate={sampling_rate}")
			rate, rx_rate_pps, tx_rate_pps = util.find_stable_throughput(tofino, engine, kitnet, tg_dpdk, testbed, test)
			
			if attack not in results:
				results[attack] = []
			
			results[attack].append((sampling_rate, rate, rx_rate_pps, tx_rate_pps))

		sampling_rate *= 2
	
	if not os.path.exists(TEST_RESULTS_DIR):
		os.makedirs(TEST_RESULTS_DIR)
	
	for attack in results.keys():
		report_file = f'{TEST_RESULTS_DIR}/{attack}.csv'
		with open(report_file, 'w') as f:
			f.write(f'# sampling rate,tg rate (%),rx rate (pps),tx rate (pps)\n')

			for sampling_rate, rate, rx_rate_pps, tx_rate_pps in results[attack]:
				f.write(f'{sampling_rate},{rate},{rx_rate_pps},{tx_rate_pps}\n')
