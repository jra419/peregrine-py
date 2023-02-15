#!/usr/bin/env python3

import util
import hosts
import os
import argparse
import glob
import statistics

import numpy as np
from plots import mpl,plt

SCRIPT_DIR         = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR   = f'{SCRIPT_DIR}/results'
PLOT               = f'{TEST_RESULTS_DIR}/component-bench.pdf'
KITSUNE_DATA       = f'{TEST_RESULTS_DIR}/kitsune/stats.csv'
PEREGRINE_DATA_DIR = f'{TEST_RESULTS_DIR}/sampling-rate/'
REPORT_BYTES       = 162 # Bytes: 14B ethernet + 148B report header
TOFINO_RATE        = 6.4e12 # bps

COLORS = [
	'#2171B5',
	'#2171B5',
	'#50938a',
	'#74C476',
]

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

def gen_plot_log(peregrine_pp_data, peregrine_fc_data, peregrine_ad_data, kitsune_data):
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

	patterns = [ None, "/" , None , None  ]
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
	plt.savefig(PLOT, bbox_inches='tight', pad_inches=0, format="pdf")

def gen_plot_linear(peregrine_pp_data, peregrine_fc_data, peregrine_ad_data, kitsune_data):
	fig, (top_ax,bottom_ax) = plt.subplots(2, 1, sharex=True)

	bottom_sep = 3e6
	top_sep    = 100e9

	x = np.arange(4)
	
	bps = [
		peregrine_pp_data[0],
		peregrine_fc_data[0],
		peregrine_ad_data[0],
		kitsune_data[0]
	]

	bottom_bps = [ v if v <= bottom_sep else top_sep for v in bps ]
	top_bps    = [ v if v >= top_sep else 0 for v in bps ]
	assert not [ v for v in bps if bottom_sep < v < top_sep ]

	bps_err = [
		peregrine_pp_data[1],
		peregrine_fc_data[1],
		peregrine_ad_data[1],
		kitsune_data[1]
	]

	bottom_bps_err = [ err if v <= bottom_sep else 0 for v,err in zip(bps,bps_err) ]
	top_bps_err    = [ err if v >= top_sep else 0 for v,err in zip(bps,bps_err) ]
	assert not [ err for v,err in zip(bps,bps_err) if bottom_sep < v < top_sep ]

	bar_labels = [
		'Peregrine PP',
		'Peregrine FC',
		'Peregrine MD',
		'Kitsune',
	]

	bottom_ax.spines['top'].set_visible(False)
	top_ax.spines['bottom'].set_visible(False)

	top_ax.tick_params(axis='x', which='both', bottom=False)

	bottom_ax.set_ylim(0, bottom_sep)
	top_ax.set_ylim(top_sep, 10e12)

	bottom_ax.set_yticks([ 0, 1e6, 2e6, 3e6 ])
	top_ax.set_yticks([ 1e12, 5e12, 10e12 ])

	bottom_ax.set_yticklabels([ '0', '1Mbps', '2Mbps', '3Mbps' ])
	top_ax.set_yticklabels([ '1Tbps', '5Tbps', '10Tbps' ])

	patterns = [ None, "/" , None , None  ]

	print('bottom', bottom_bps)
	print('top', top_bps)

	bottom_bars = bottom_ax.bar(x, bottom_bps,
		yerr=bottom_bps_err,
		width=0.5,
		label=bar_labels,
		color=COLORS,
		edgecolor='black',
		hatch=patterns
	)

	top_bars = top_ax.bar(x, top_bps,
		yerr=top_bps_err,
		width=0.5,
		label=bar_labels,
		color=COLORS,
		edgecolor='black',
		hatch=patterns
	)
	
	bottom_ax.set_ylabel('Throughput')
	# bottom_ax.yaxis.set_label_coords(-0.13,1.1)
	bottom_ax.yaxis.set_label_coords(-0.21,1.15)

	plt.tick_params(
		axis='x',
		which='both',
		bottom=False,
		top=False,
		labelbottom=False
	)

	d = .015  
	kwargs = dict(transform=top_ax.transAxes, color='k', clip_on=False)
	top_ax.plot((-d, +d), (-d, +d), **kwargs)      
	top_ax.plot((1 - d, 1 + d), (-d, +d), **kwargs)
	kwargs.update(transform=bottom_ax.transAxes)  
	bottom_ax.plot((-d, +d), (1 - d, 1 + d), **kwargs)  
	bottom_ax.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

	for b1, b2 in zip(top_bars, bottom_bars):
		posx = b2.get_x() + b2.get_width()/2.
		if b2.get_height() > bottom_sep:
			bottom_ax.plot((posx-3*d, posx+3*d), (1 - d, 1 + d), color='k', clip_on=False,
				transform=bottom_ax.get_xaxis_transform())
		if b1.get_height() > top_sep:
			top_ax.plot((posx-3*d, posx+3*d), (- d, + d), color='k', clip_on=False,
				transform=top_ax.get_xaxis_transform())

	# bottom_ax.legend(bbox_to_anchor=(0.5, 2.2))
	bottom_ax.legend(loc="upper left", bbox_to_anchor=(-0.2, 2.8), ncols=2)

	# plt.show()
	plt.savefig(PLOT, bbox_inches='tight', pad_inches=0, format="pdf")

def plot():
	peregrine_pp_data = (TOFINO_RATE, 0)
	peregrine_fc_data = (TOFINO_RATE, 0)
	peregrine_ad_data = get_peregrine_ad_data()
	kitsune_data      = get_kitsune_data()

	print('Peregrine:', peregrine_ad_data)
	print('Kitsune:  ', kitsune_data)
	
	# gen_plot_log(
	# 	peregrine_pp_data,
	# 	peregrine_fc_data,
	# 	peregrine_ad_data,
	# 	kitsune_data
	# )

	gen_plot_linear(
		peregrine_pp_data,
		peregrine_fc_data,
		peregrine_ad_data,
		kitsune_data
	)

if __name__ == '__main__':
	plot()