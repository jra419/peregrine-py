#!/usr/bin/env python3

import hosts
import json
import os

SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
TESTBED_JSON = f'{SCRIPT_DIR}/testbed.json'
VERBOSE      = True

def get_testbed_cfg():
	with open(TESTBED_JSON, 'r') as f:
		testbed = json.load(f)
		return testbed

if __name__ == '__main__':
	testbed = get_testbed_cfg()

	tofino = hosts.Tofino(
		hostname=testbed['tofino']['hostname'],
		peregrine_path=testbed['tofino']['peregrine-path'],
		verbose=VERBOSE
	)
	
	# engine = hosts.Engine(
	# 	hostname=testbed['engine']['hostname'],
	# 	peregrine_path=testbed['engine']['peregrine-path'],
	# 	verbose=VERBOSE
	# )

	# kitnet = hosts.KitNet(
	# 	hostname=testbed['plugins']['kitnet']['hostname'],
	# 	peregrine_path=testbed['plugins']['kitnet']['peregrine-path'],
	# 	verbose=VERBOSE
	# )

	tg = hosts.TG_kernel(
		hostname=testbed['tg']['hostname'],
		verbose=VERBOSE
	)

	test_duration_seconds = 10 # seconds

	tests = [
		{
			"attack": "os-scan",
			"sampling-rate": 1024,
			# "pcap": f"{testbed['tg']['pcaps-path']}/os-scan-exec.pcap",
			"pcap": f"/home/fcp/bench/pcaps/uniform_64B_1000_flows.pcap",
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
		print(f"[*] attack={test['attack']} sampling-rate={test['sampling-rate']}")

		tofino.start(test['sampling-rate'])
		engine.start(testbed['engine']['listen-iface'])

		kitnet.start(
			test['models']['fm'],
			test['models']['el'],
			test['models']['ol'],
			test['models']['ts'],
		)

		tg.run(test['pcap'], testbed['tg']['tx-kernel-iface'], test_duration_seconds)

		tofino.stop()
		engine.stop()
		kitnet.stop()

		tofino.get_report()
		engine.get_report()