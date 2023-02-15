#!/usr/bin/env python3

import util
import hosts
import os
import argparse
import glob

import numpy as np
from plots import mpl,plt,attacks,attacks_prettyfied

SCRIPT_DIR       = os.path.dirname(os.path.realpath(__file__))
TEST_RESULTS_DIR = f'{SCRIPT_DIR}/results'
PLOT             = f'{TEST_RESULTS_DIR}/kitsune-fc-vs-ad.pdf'
KITSUNE_DATA     = f'{TEST_RESULTS_DIR}/kitsune/results.csv'

COLORS = [
	'#2171B5',
	'#74C476',
]

def get_data():
	data = {}

	with open(KITSUNE_DATA, 'r') as f:
		lines = f.readlines()

		for line in lines:
			line = line.rstrip('\n')
			line = line.split(',')

			attack = line[0]
			dt_fe  = float(line[3])
			dt_ad  = float(line[4])

			dt_total  = dt_fe + dt_ad
			dt_fe_perc = 100 * dt_fe / dt_total
			dt_ad_perc = 100 * dt_ad / dt_total

			data[attack] = (dt_fe_perc, dt_ad_perc)		
		
	return data

def gen_plot(data):
	fig, ax = plt.subplots()

	y_pos = np.arange(len(attacks))

	dt_fes_perc = [ data[attack][0] for attack in attacks ]
	dt_ads_perc = [ data[attack][1] for attack in attacks ]

	dt_fes_labels = [ f'{v:.1f}\%' if v > 5 else '' for v in dt_fes_perc ]
	dt_ads_labels = [ f'{v:.1f}\%' if v > 5 else '' for v in dt_ads_perc ]

	p = ax.barh(y_pos, dt_fes_perc, color=COLORS[0], label='FC')
	ax.bar_label(p, labels=dt_fes_labels, label_type='center', fontsize=7)

	p = ax.barh(y_pos, dt_ads_perc, color=COLORS[1], label='MD', left=dt_fes_perc)
	ax.bar_label(p, labels=dt_ads_labels, label_type='center', fontsize=7)

	ax.set_yticks(y_pos)
	ax.set_yticklabels([ attacks_prettyfied[a] for a in attacks ], rotation=25, ha='right')
	# ax.set_yticklabels(attacks)
	ax.invert_yaxis()

	ax.set_xlabel('Total processing time (\%)')
	ax.set_xlim([0, 100])

	ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncols=2)

	# plt.show()
	plt.savefig(PLOT, bbox_inches='tight', pad_inches=0, format="pdf")

def plot():
	data = get_data()
	gen_plot(data)

if __name__ == '__main__':
	plot()