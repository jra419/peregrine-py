#!/usr/bin/env python3

import util
import hosts
import os
import argparse
import subprocess
import statistics

SCRIPT_DIR           = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR     = f'{SCRIPT_DIR}/results/kitsune'
TEST_RESULTS         = f'{TEST_RESULTS_DIR}/results.csv'
TEST_STATS           = f'{TEST_RESULTS_DIR}/stats.csv'
KITSUNE_DIR          = f'{SCRIPT_DIR}/../sota/kitsune'
KITSUNE_BENCH_SCRIPT = f'{KITSUNE_DIR}/bench.sh'

def run_benchmarks(attacks, pcaps_dir):
	results = []

	for attack in attacks:
		pcap = f"{pcaps_dir}/{attack['pcap']}"
		assert '.pcap' in pcap
		name = attack['attack']

		pcap_basename = pcap.split('/')[-1].split('.pcap')[0]
		csv           = f"{TEST_RESULTS_DIR}/{pcap_basename}.csv"

		print(f"[*] attack={name}")

		cmd = [ KITSUNE_BENCH_SCRIPT, pcap ]

		proc = subprocess.run(cmd,
			cwd=TEST_RESULTS_DIR,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)

		assert proc.returncode == 0

		with open(csv, 'r') as f:
			lines = f.readlines()
			assert len(lines) >= 1
			line = lines[0].rstrip('\n')
			training_time, execution_time, pps = line.split(',')
			results.append((name, training_time, execution_time, pps))
			print(f"      rate={util.compact(int(pps))}pps")

		os.remove(csv)
	
	return results

def dump_stats():
	ppss = []

	with open(TEST_RESULTS, 'r') as f:
		lines = f.readlines()
		for line in lines:
			line = line.rstrip('\n')
			line = line.split(',')

			if not line: continue
			assert len(line) == 4

			name = line[0]
			training_time = line[1]
			execution_time = line[2]
			pps = int(line[3])
			ppss.append(pps)

	with open(TEST_STATS, 'w') as f:
		if len(ppss) == 1:
			m     = ppss[0]
			mean  = ppss[0]
			stdev = 0
			M     = ppss[0]
		else:
			m     = min(ppss)
			mean  = statistics.mean(ppss)
			stdev = statistics.stdev(ppss)
			M     = max(ppss)

		f.write(f"{m},{mean},{stdev},{M}\n")	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Benchmark Kitsune')

	parser.add_argument('--attack', type=str, required=False, help='Target attack')
	parser.add_argument('--pcaps-dir', type=str, required=False, default=SCRIPT_DIR, help='Path to pcaps')

	parser.add_argument('--skip-bench',
		required=False,
		action='store_true',
		help='Skip benchmarks'
	)

	args = parser.parse_args()

	tests        = util.get_tests()
	target_tests = [ t for t in tests if not args.attack or args.attack == t['attack'] ]

	if not os.path.exists(TEST_RESULTS_DIR):
		os.makedirs(TEST_RESULTS_DIR)
	
	if not args.skip_bench:
		results = run_benchmarks(target_tests, args.pcaps_dir)

		with open(TEST_RESULTS, 'w') as f:
			for attack, training_time, execution_time, pps in results:
				f.write(f'{attack},{training_time},{execution_time},{pps}\n')
	
	dump_stats()