#!/usr/bin/env python3

import os
import shutil
import json

SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
TESTBED_JSON = f'{SCRIPT_DIR}/testbed.json'
TESTS_JSON   = f'{SCRIPT_DIR}/tests.json'

DURATION_SECONDS     = 10
MAX_RETRIES          = 5
SEARCH_ITERATIONS    = 10
RATE_LOWER_THRESHOLD = 0.1
LOSS_THRESHOLD       = 0.001

def get_testbed_cfg():
	with open(TESTBED_JSON, 'r') as f:
		testbed = json.load(f)
		return testbed

def get_tests():
	with open(TESTS_JSON, 'r') as f:
		tests = json.load(f)
		return tests

def get_test(attack):
	data  = None
	tests = get_tests()

	for test in tests['tests']:
		if attack == test['attack']:
			data = test
			break

	if not data:
		print(f'Error: attack {attack} not found in {TESTS_JSON}')
		exit(1)
	
	return data

def compact(n):
	orders = [
		(1e9, 1e9, 'G'),
		(1e6, 1e6, 'M'),
		(1e3, 1e3, 'K'),
		(0, 1, ''),
	]

	for o in orders:
		if n >= o[0]:
			return f'{n/o[1]:.1f}{o[2]}'
	
	return n
	
def get_data_from_controller(controller_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		ports_info = lines[1:]
		stats_port = int(ports_info[-1].split('\t')[0])

		rx_pkts    = -1
		tx_samples = -1

		for port_info in ports_info:
			port_info = port_info.split('\t')
			port      = int(port_info[0])
			rx        = int(port_info[1])
			tx        = int(port_info[2])

			if port != stats_port:
				rx_pkts += rx
			else:
				tx_samples = tx
				if rx_pkts > 0 and tx_samples > 0:
					return rx_pkts,tx_samples
				else:
					return -1,-1
		return rx_pkts,tx_samples

def get_processed_samples_from_dispatcher(dispatcher_report_file):
	with open(dispatcher_report_file, 'r') as f:
		lines = f.readlines()
		samples = lines[1:]
		return len(samples)

def run(tofino, dispatcher, kitnet, tg_dpdk, testbed, test, rate):
	controller_report_file = None
	dispatcher_report_file     = None

	rx_pkts    = -1
	tx_samples = -1
	processed  = -1
	loss       = -1

	success = False
	try_run = 0
	while not success:
		try_run += 1

		if try_run > MAX_RETRIES:
			print('Maximum number of allowed retries reached. Exiting.')
			exit(1)

		tofino.start()
		dispatcher.start(testbed['dispatcher']['listen-iface'])
		kitnet.start(
			test['models']['fm'],
			test['models']['el'],
			test['models']['ol'],
			test['models']['ts'],
		)

		tg_dpdk.run(test['pcap'], testbed['tg']['tx-dpdk-port'], rate, DURATION_SECONDS)

		tofino.stop()
		dispatcher.stop()
		kitnet.stop()

		controller_report_file = tofino.get_report()
		dispatcher_report_file = dispatcher.get_report()

		rx_pkts,tx_samples = get_data_from_controller(controller_report_file)
		processed          = get_processed_samples_from_dispatcher(dispatcher_report_file)
		loss               = abs(tx_samples - processed) / tx_samples

		if processed > tx_samples:
			print(f"  WARNING: too many samples received (tx {tx_samples} | samples {processed}")
		success = rx_pkts > -1 and tx_samples > -1

		if not success:
			print(f"  - Packets not flowing through Tofino. Repeating experiment.")
		
	assert rx_pkts > 0
	assert tx_samples > 0

	os.remove(controller_report_file)
	os.remove(dispatcher_report_file)

	rx_rate_pps = int(rx_pkts / DURATION_SECONDS)
	tx_rate_pps = int(tx_samples / DURATION_SECONDS)

	return rx_rate_pps, tx_rate_pps, loss

def find_stable_throughput(tofino, dispatcher, kitnet, tg_dpdk, testbed, test, verbose=True):
	upper_bound = 100.0
	lower_bound = 0
	i           = 0

	max_rate = upper_bound
	mid_rate = upper_bound
	min_rate = lower_bound

	best_rate        = -1
	best_rx_rate_pps = -1
	best_tx_rate_pps = -1
	best_loss        = -1

	while True:
		rate = mid_rate

		if rate < RATE_LOWER_THRESHOLD or i >= SEARCH_ITERATIONS:
			break
		
		rx_rate_pps, tx_rate_pps, loss = run(tofino, dispatcher, kitnet, tg_dpdk, testbed, test, rate)

		if verbose:
			print(f'  [{i+1:2d}/{SEARCH_ITERATIONS}] rate {rate:3.2f}% rx {compact(rx_rate_pps)}pps tx {compact(tx_rate_pps)}pps loss {100 * loss:.2f}%')

		if loss < LOSS_THRESHOLD:
			if tx_rate_pps > best_tx_rate_pps:
				best_rate        = rate
				best_rx_rate_pps = rx_rate_pps
				best_tx_rate_pps = tx_rate_pps
				best_loss        = loss

			if mid_rate == upper_bound or i + 1 >= SEARCH_ITERATIONS:
				break

			min_rate = mid_rate
			mid_rate = mid_rate + (max_rate - mid_rate) / 2
		else:
			max_rate = mid_rate
			mid_rate = min_rate + (mid_rate - min_rate) / 2
		
		i += 1
	
	if verbose:
		print(f'  Best rate {best_rate:3.2f}% rx {compact(best_rx_rate_pps)}pps tx {compact(best_tx_rate_pps)}pps loss {100 * best_loss:.2f}%')

	return best_rate, best_rx_rate_pps, best_tx_rate_pps