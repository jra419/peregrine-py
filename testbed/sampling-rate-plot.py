#!/usr/bin/env python3

import os
import glob

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

SCRIPT_DIR        = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR  = f'{SCRIPT_DIR}/results/sampling-rate'
PLOT              = f'{SCRIPT_DIR}/results/sampling-rate/sampling-rate.png'

def get_data():
	data_files_pattern = f'{TEST_RESULTS_DIR}/*.csv'
	data_files = glob.glob(data_files_pattern)
	
	data = {}

	for data_file in data_files:
		basename = os.path.basename(data_file)
		attack   = os.path.splitext(basename)[0]

		data[attack] = []

		with open(data_file, 'r') as f:
			lines = f.readlines()

			for line in lines:
				if line and line[0] == '#':
					continue

				line = line.rstrip().split(',')
				assert len(line) == 4

				sampling_rate = int(line[0])
				tg_rate       = float(line[1])
				rx_rate_pps   = int(line[2])
				tx_rate_pps   = int(line[3])

				data[attack].append((sampling_rate,tg_rate,rx_rate_pps,tx_rate_pps))
		
	return data

def get_sampling_rate_range(data):
	min_sampling_rate = -1
	max_sampling_rate = -1
	
	for attack in data.keys():
		for sampling_rate,_,_,_ in data[attack]:
			min_sampling_rate = min(min_sampling_rate, sampling_rate)
			max_sampling_rate = max(max_sampling_rate, sampling_rate)
	
	return min_sampling_rate, max_sampling_rate

def plot(data):
	fig = plt.figure()
	
	plt.clf()

	ax = fig.add_subplot(111)
	ax.set_aspect(1)

	min_sampling_rate, max_sampling_rate = get_sampling_rate_range(data)

	min_rate = 0
	max_rate = 100
	
	attacks        = list(data.keys())
	sampling_rates = []
	matrix         = [ [] for _ in range(len(attacks)) ]

	for i, attack in enumerate(attacks):
		attack_vector = data[attack]
		attack_vector.sort(key=lambda v: v[0])

		for sampling_rate,tg_rate,rx_rate_pps,tx_rate_pps in attack_vector:
			matrix[i].append(tg_rate)
			sampling_rates = list(set(sampling_rates + [ sampling_rate ]))

	print('Sampling rates', sampling_rates)
	print('Attacks', attacks)

	width  = len(sampling_rates)
	height = len(attacks)

	# colormap = plt.cm.jet
	colormap = mpl.colormaps['RdYlGn']
	
	nodes = [ 0.0, 0.5, 1.0 ]
	colors = [ 'red', 'yellow', 'green' ]
	cmap = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
	cmap.set_under('black')

	res = ax.imshow(matrix, cmap=cmap, vmin=min_rate, vmax=max_rate, interpolation='nearest')

	for x in range(width):
		for y in range(height):
			gbps = matrix[x][y]
			ax.annotate(f'{gbps:.2f}G', xy=(y,x), va='center', ha='center')

	cbar = fig.colorbar(res, ticks=[ 0, 25, 50, 75, 100 ])
	cbar.ax.set_yticklabels([ '0G', '25G', '50G', '75G', '100G' ])

	plt.xticks(range(width), sampling_rates)
	plt.yticks(range(height), attacks)

	plt.savefig(PLOT)
	plt.show()

if __name__ == '__main__':
	data = get_data()
	plot(data)