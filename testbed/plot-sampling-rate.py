#!/usr/bin/env python3

import util
import hosts
import os
import argparse
import glob
import statistics

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

SCRIPT_DIR        = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR  = f'{SCRIPT_DIR}/results'
PLOT              = f'{TEST_RESULTS_DIR}/sampling-rate-summary.png'
SAMPLING_RATE_DIR = f'{TEST_RESULTS_DIR}/sampling-rate/'

COLOR = '#2171B5'

def get_data():
	data_files_pattern = f'{SAMPLING_RATE_DIR}/*.csv'
	data_files = glob.glob(data_files_pattern)
	
	data = {}

	for data_file in data_files:
		basename = os.path.basename(data_file)
		attack   = os.path.splitext(basename)[0]

		with open(data_file, 'r') as f:
			lines = f.readlines()
			bps = -1
			for line in lines:
				if line and line[0] == '#':
					continue

				line = line.rstrip().split(',')
				assert len(line) == 5

				sampling_rate = int(line[0])
				tg_rate       = float(line[1])
				rx_rate_bps   = int(line[2])
				rx_rate_pps   = int(line[3])
				tx_rate_pps   = int(line[4])

				if sampling_rate not in data:
					data[sampling_rate] = []
				
				data[sampling_rate].append(rx_rate_bps)

	stats = []
	for sampling_rate in data.keys():
		bps = data[sampling_rate]
			
		if len(data) > 1:
			avg   = statistics.mean(bps)
			stdev = statistics.stdev(bps)
		else:
			avg   = bps[0]
			stdev = 0

		stats.append((sampling_rate, avg, stdev))
	
	return stats

def gen_plot(data):
	fig, ax = plt.subplots()

	x = np.arange(4)

	sampling_rates = [ f'1/{d[0]}' for d in data ]
	bps_avg        = [ d[1]/1e9 for d in data ]
	bps_err        = [ d[2]/1e9 for d in data ]

	colors = [ COLOR for _ in sampling_rates ]
	labels = [ f'1/{sr}' for sr in sampling_rates ]

	ax.bar(sampling_rates, bps_avg, yerr=bps_err, color=colors)
	
	ax.set_ylabel('Throughput (Gbps)')
	ax.set_xlabel('Sampling rate')
	ax.tick_params(axis='x', labelrotation=-45)
	ax.set_yticks( [ 0, 20, 40, 60, 80, 100 ])
	
	# plt.show()
	plt.savefig(PLOT, bbox_inches='tight')

def plot():
	data = get_data()
	print(data)
	gen_plot(data)

if __name__ == '__main__':
	plot()