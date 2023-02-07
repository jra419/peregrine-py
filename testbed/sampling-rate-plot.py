#!/usr/bin/env python3

import os
import glob

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from util import compact

SCRIPT_DIR        = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR  = f'{SCRIPT_DIR}/results/sampling-rate'
PLOT_PPS          = f'{SCRIPT_DIR}/results/sampling-rate/sampling-rate-pps.png'
PLOT_BPS          = f'{SCRIPT_DIR}/results/sampling-rate/sampling-rate-bps.png'

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

def plot(data, plot_file, pps=False, bps=False):
	assert pps or bps

	fig = plt.figure()
	
	plt.clf()

	ax = fig.add_subplot(111)
	ax.set_aspect(1)

	min_sampling_rate, max_sampling_rate = get_sampling_rate_range(data)

	if bps:
		vmin = 0
		vmax = 100
		# units = 'Gbps'
		units = '%'
	else:
		vmin = 0
		vmax = int(50e6)
		units = 'pps'
	
	attacks        = sorted(list(data.keys()))
	sampling_rates = []
	matrix         = [ [] for _ in range(len(attacks)) ]

	for i, attack in enumerate(attacks):
		attack_vector = data[attack]
		attack_vector.sort(key=lambda v: v[0])

		for sampling_rate,tg_rate,rx_rate_pps,tx_rate_pps in attack_vector:
			if pps: matrix[i].append(rx_rate_pps)
			else:   matrix[i].append(tg_rate)

			sampling_rates = list(set(sampling_rates + [ sampling_rate ]))

	print('Sampling rates', sampling_rates)
	print('Attacks', attacks)
	for row in matrix:
		print(row)

	# colormap = plt.cm.jet
	colormap = mpl.colormaps['RdYlGn']
	
	nodes  = [ 0.0, 0.5, 1.0 ]
	colors = [ 'crimson', 'yellow', 'mediumseagreen' ]
	cmap   = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
	cmap.set_under('black')

	res = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='nearest', aspect='auto')

	for x in range(len(matrix)):
		for y in range(len(matrix[x])):
			pps = matrix[x][y]
			ax.annotate(f'{compact(pps, no_decimal=True)}{units}', xy=(y,x), va='center', ha='center')

	n_ticks = 6
	ticks = []
	labels = []
	for i in range(n_ticks):
		tick = int(vmax*i/(n_ticks-1))
		ticks.append(tick)
		labels.append(f'{compact(tick, no_decimal=pps)}{units}')

	print('ticks', ticks)
	print('labels', labels)

	cbar = fig.colorbar(res, ticks=ticks)
	cbar.ax.set_yticklabels(labels)

	width  = len(sampling_rates)
	height = len(attacks)

	plt.xticks(range(width), sampling_rates)
	plt.yticks(range(height), attacks)

	plt.savefig(plot_file, bbox_inches='tight')
	# plt.show()

if __name__ == '__main__':
	data = get_data()

	plot(data, PLOT_PPS, pps=True)
	plot(data, PLOT_BPS, bps=True)