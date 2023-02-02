#!/usr/bin/env python3

from hosts.Tofino import Tofino
from hosts.Engine import Engine
from hosts.KitNet import KitNet
from hosts.TG_DPDK import TG_DPDK

import json
import os
import shutil

SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
TESTBED_JSON = f'{SCRIPT_DIR}/testbed.json'
VERBOSE      = False
PCAP_TX_DURATION_SECONDS = 10
SAMPLING_RATE            = 1024
MAX_RETRIES              = 5

def get_testbed_cfg():
	with open(TESTBED_JSON, 'r') as f:
		testbed = json.load(f)
		return testbed

def get_data_from_controller(controller_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		ports_info = lines[1:]
		stats_port = int(ports_info[-1].split('\t')[0])

		total_rx = 0
		total_tx = 0

		for port_info in ports_info:
			port_info = port_info.split('\t')
			port      = int(port_info[0])
			rx        = int(port_info[1])
			tx        = int(port_info[2])

			if port != stats_port:
				total_rx += rx
				total_tx += tx
			else:
				tx_stats_port = tx
				return total_rx,total_tx if total_tx == tx_stats_port and total_tx > 0 else -1
		return total_rx,total_tx

def get_processed_samples_from_engine(engine_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		samples = lines[1:]
		return len(samples)

def run(tofino, engine, kitnet, tg_dpdk, testbed, test):
	print(f"[*] attack={test['attack']}")

	controller_report_file = None
	engine_report_file     = None

	controller_rx     = -1
	controller_tx     = -1
	processed_samples = -1

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

		tg_dpdk.run(test['pcap'], testbed['tg']['tx-dpdk-port'], PCAP_TX_DURATION_SECONDS)

		tofino.stop()
		engine.stop()
		kitnet.stop()

		controller_report_file = tofino.get_report()
		engine_report_file     = engine.get_report()

		controller_rx,controller_tx = get_data_from_controller(controller_report_file)
		processed_samples           = get_processed_samples_from_engine(engine_report_file)

		if controller_rx == -1 or controller_tx == -1:
			print(f"  - Packets not flowing through Tofino. Repeating experiment.")
	
	assert controller_rx > 0
	assert controller_tx > 0

	print(f'Controller RX     {controller_rx}')
	print(f'Controller TX     {controller_tx}')
	print(f'Processed samples {processed_samples} ({processed_samples * 100.0 / controller_tx:.2f} %)')

	os.remove(controller_report_file)
	os.remove(engine_report_file)

if __name__ == '__main__':
	testbed = get_testbed_cfg()

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

	tests = [
		{
			"attack": "os-scan",
			"pcap": f"{testbed['tg']['pcaps-path']}/os-scan-exec.pcap",
			"models": {
				"fm": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-fm.txt",
				"el": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-el.txt",
				"ol": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-ol.txt",
				"ts": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-train-stats.txt",
			}
		}
	]

	# print('[*] Installing')
	# tofino.modify_sampling_rate(SAMPLING_RATE)
	# tofino.install()

	for test in tests:
		run(tofino, engine, kitnet, tg_dpdk, testbed, test)