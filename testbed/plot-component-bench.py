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

SCRIPT_DIR         = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR   = f'{SCRIPT_DIR}/results'
PLOT               = f'{TEST_RESULTS_DIR}/component-bench.png'
KITSUNE_DATA       = f'{TEST_RESULTS_DIR}/kitsune/stats.csv'
PEREGRINE_DATA_DIR = f'{TEST_RESULTS_DIR}/sampling-rate/'
REPORT_BYTES       = 162 # Bytes: 14B ethernet + 148B report header
TOFINO_RATE        = 6.4e12 # bps

COLORS = [
	'#2171B5',
	'#2171B5',
	'#2171B5',
	'#74C476',
]

# COLORS = [
# 	'#ff7b59',
# 	'#ffb66c',
# 	'#50938a',
# 	'#74C476',
# ]

def get_kitsune_data():
	with open(KITSUNE_DATA, 'r') as f:
		lines = f.readlines()
		assert len(lines) == 1

		line = lines[0]
		line = line.rstrip('\n')
		line = line.split(',')

		assert len(line) == 8

		pps_avg   = int(line[1])
		pps_stdev = int(line[2])

		# To compare Kitsune and Peregrine in a fair way,
		# let's assume the same packet sizes.
		bps_avg   = pps_avg * REPORT_BYTES * 8
		bps_stdev = pps_stdev * REPORT_BYTES * 8
		
		return bps_avg, bps_stdev

def get_peregrine_ad_data():
	data_files_pattern = f'{PEREGRINE_DATA_DIR}/*.csv'
	data_files = glob.glob(data_files_pattern)
	
	data = []

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

				bps = max(bps, tx_rate_pps * REPORT_BYTES * 8)

			assert bps >= 0
			data.append(bps)

	if len(data) > 1:
		return statistics.mean(data), statistics.stdev(data)
	return data[0], 0

def gen_plot(peregrine_pp_data,	peregrine_fc_data, peregrine_ad_data, kitsune_data):
	fig, ax = plt.subplots()

	x = np.arange(4)
	
	bps = [
		peregrine_pp_data[0],
		peregrine_fc_data[0],
		peregrine_ad_data[0],
		kitsune_data[0]
	]

	bps_err = [
		peregrine_pp_data[1],
		peregrine_fc_data[1],
		peregrine_ad_data[1],
		kitsune_data[1]
	]

	bar_labels = [
		'Peregrine Packet Processing',
		'Peregrine Feature Computation',
		'Peregrine ML-based Detection',
		'Kitsune',
	]

	patterns = [ None, "/" , "x" , None  ]
	# patterns = [ None for _ in range(len(bps)) ]
	ax.bar(x, bps,
		yerr=bps_err,
		width=0.5,
		label=bar_labels,
		color=COLORS,
		edgecolor='black',
		hatch=patterns
	)
	
	ax.set_yscale('log')
	ax.set_ylabel('Throughput')
	ax.set_yticks([ 1, 1e3, 1e6, 1e9, 1e12 ])
	ax.set_yticklabels([ '', 'Kbps', 'Mbps', 'Gbps', 'Tbps' ])

	ax.yaxis.set_label_coords(-0.12, 0.6)

	plt.tick_params(
		axis='x',
		which='both',
		bottom=False,
		top=False,
		labelbottom=False
	)

	ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncols=2)

	# plt.show()
	plt.savefig(PLOT, bbox_inches='tight')

def plot():
	peregrine_pp_data = (TOFINO_RATE, 0)
	peregrine_fc_data = (TOFINO_RATE, 0)
	peregrine_ad_data = get_peregrine_ad_data()
	kitsune_data      = get_kitsune_data()

	print('Peregrine:', peregrine_ad_data)
	print('Kitsune:  ', kitsune_data)
	
	gen_plot(
		peregrine_pp_data,
		peregrine_fc_data,
		peregrine_ad_data,
		kitsune_data
	)

if __name__ == '__main__':
	plot()