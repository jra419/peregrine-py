#!/usr/bin/env python3

import util
import hosts
import os
import argparse
import glob

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

SCRIPT_DIR       = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR = f'{SCRIPT_DIR}/results'
PLOT             = f'{TEST_RESULTS_DIR}/component-bench.png'
KITSUNE_DATA     = f'{TEST_RESULTS_DIR}/kitsune/stats.csv'
PEREGRINE_DATA   = f'{TEST_RESULTS_DIR}/sampling-rate/stats.csv'

def get_kitsune_data():
	with open(KITSUNE_DATA, 'r') as f:
		lines = f.readlines()
		assert len(lines) == 1

		line = lines[0]
		line = line.rstrip('\n')
		line = line.split(',')

		assert len(line) == 8

		bps_m     = int(line[4])
		bps_avg   = int(line[5])
		bps_stdev = int(line[6])
		bps_M     = int(line[7])
		
		return bps_avg, bps_stdev

def gen_plot(data, plot_file, pps=False, bps=False):
	assert pps or bps

	fig = plt.figure()
	plt.clf()

	ax = fig.add_subplot(111)
	ax.set_aspect(1)

	min_sampling_rate, max_sampling_rate = get_sampling_rate_range(data)

	if bps:
		vmin = 0
		vmax = int(100e9)
		units = 'bps'
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

		for sampling_rate,tg_rate,rx_rate_bps,rx_rate_pps,tx_rate_pps in attack_vector:
			if pps: matrix[i].append(rx_rate_pps)
			else:   matrix[i].append(rx_rate_bps)

			sampling_rates = list(set(sampling_rates + [ sampling_rate ]))

	# print('Sampling rates', sampling_rates)
	# print('Attacks', attacks)

	# colormap = plt.cm.jet
	colormap = mpl.colormaps['RdYlGn']
	
	nodes  = [ 0.0, 0.5, 1.0 ]
	colors = [ 'crimson', 'yellow', 'mediumseagreen' ]
	cmap   = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
	cmap.set_under('black')

	res = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='nearest', aspect='auto')

	for x in range(len(matrix)):
		for y in range(len(matrix[x])):
			v = matrix[x][y]
			ax.annotate(f'{util.compact(v, no_decimal=True)}{units}', xy=(y,x), va='center', ha='center')

	n_ticks = 6
	ticks = []
	labels = []
	for i in range(n_ticks):
		tick = int(vmax*i/(n_ticks-1))
		ticks.append(tick)
		labels.append(f'{util.compact(tick, no_decimal=True)}{units}')

	cbar = fig.colorbar(res, ticks=ticks)
	cbar.ax.set_yticklabels(labels)

	width  = len(sampling_rates)
	height = len(attacks)

	plt.xticks(range(width), sampling_rates)
	plt.yticks(range(height), attacks)

	plt.savefig(plot_file, bbox_inches='tight')
	# plt.show()

def plot():
	peregrine_pp_data = (1e12, 0)
	peregrine_fc_data = (1e12, 0)
	peregrine_ad_data = (1e12, 0)
	kitsune_data = get_kitsune_data()
	print(kitsune_data)

	# if not data:
	# 	print('No data.')
	# 	exit(0)

	# print('Generating pps plot')
	# gen_plot(data, PLOT_PPS, pps=True)

	# print('Generating bps plot')
	# gen_plot(data, PLOT_BPS, bps=True)

	print('Done')

if __name__ == '__main__':
	plot()