#!/usr/bin/env python3

import hosts
import json
import os

SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
TESTBED_JSON = f'{SCRIPT_DIR}/testbed.json'
VERBOSE      = False

def get_testbed_cfg():
	with open(TESTBED_JSON, 'r') as f:
		testbed = json.load(f)
		return testbed

def check_success_from_controller_report(controller_report_file):
	with open(controller_report_file, 'r') as f:
		lines = f.readlines()
		assert(len(lines) > 1)

		ports_info = lines[1:]
		stats_port = int(ports_info[-1].split('\t')[0])

		samples_sent = 0
		for port_info in ports_info:
			port_info = port_info.split('\t')
			port = int(port_info[0])
			rx = int(port_info[1])
			tx = int(port_info[2])

			if port != stats_port:
				samples_sent += tx
			else:
				return samples_sent == tx and samples_sent > 0
		return True

def run(tofino, engine, kitnet, tg, testbed, test, duration_seconds):
	print(f"[*] attack={test['attack']} sampling-rate={test['sampling-rate']}")

	print(f"  - Setting sampling rate")
	tofino.modify_sampling_rate(test['sampling-rate'])
	
	print(f"  - Installing")
	tofino.install()

	success = False
	while not success:
		print(f"  - Starting Tofino")
		tofino.start()

		print(f"  - Starting Engine")
		engine.start(testbed['engine']['listen-iface'])

		print(f"  - Starting KitNet module")
		kitnet.start(
			test['models']['fm'],
			test['models']['el'],
			test['models']['ol'],
			test['models']['ts'],
		)

		print(f"  - Transmitting pcap")
		tg.run(test['pcap'], testbed['tg']['tx-kernel-iface'], duration_seconds)

		tofino.stop()
		engine.stop()
		kitnet.stop()

		controller_report_file = tofino.get_report()
		engine_report_file     = engine.get_report()

		success = check_success_from_controller_report(controller_report_file)

		if not success:
			print(f"  - Packets not flowing through Tofino. Repeating experiment.")

if __name__ == '__main__':
	testbed = get_testbed_cfg()

	tofino = hosts.Tofino(
		hostname=testbed['tofino']['hostname'],
		peregrine_path=testbed['tofino']['peregrine-path'],
		verbose=VERBOSE
	)
	
	engine = hosts.Engine(
		hostname=testbed['engine']['hostname'],
		peregrine_path=testbed['engine']['peregrine-path'],
		verbose=VERBOSE
	)

	kitnet = hosts.KitNet(
		hostname=testbed['plugins']['kitnet']['hostname'],
		peregrine_path=testbed['plugins']['kitnet']['peregrine-path'],
		verbose=VERBOSE
	)

	tg = hosts.TG_kernel(
		hostname=testbed['tg']['hostname'],
		verbose=VERBOSE
	)

	duration_seconds = 10 # seconds

	tests = [
		{
			"attack": "os-scan",
			"sampling-rate": 1024,
			"pcap": f"{testbed['tg']['pcaps-path']}/os-scan-exec.pcap",
			# "pcap": f"/home/fcp/bench/pcaps/uniform_64B_1000_flows.pcap",
			"models": {
				"fm": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-fm.txt",
				"el": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-el.txt",
				"ol": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-ol.txt",
				"ts": f"{testbed['plugins']['kitnet']['models-path']}/m-10/os-scan-m-10-train-stats.txt",
			}
		}
	]

	# tofino.install()

	for test in tests:
		run(tofino, engine, kitnet, tg, testbed, test, duration_seconds)