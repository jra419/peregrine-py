#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.pyplot as plt

FONT_SIZE = 10

mpl.rcParams.update(
	{
		'font.family':     'sans-serif',
		'font.size':       FONT_SIZE,
		'axes.labelsize':  FONT_SIZE,
		'legend.fontsize': FONT_SIZE,
		'xtick.labelsize': FONT_SIZE,
		'ytick.labelsize': FONT_SIZE,
		'figure.dpi':      600,
		'figure.figsize': (3, 3),
		'text.usetex':     True,
		'text.latex.preamble': r"""
			\usepackage{libertine}
			\usepackage[libertine]{newtxmath}
			""",
	}
)

attacks = [
	'active-wiretap',
	'arp-mitm',
	'dos-syn',
	'fuzzing',
	'os-scan',
	'ssdp-flood',
	'ssl-renegotiation',
	'video-injection',
	'botnet',
	'ddos-hoic',
	'ddos-loic',
	'dos-goldeneye',
	'dos-hulk',
	'dos-slowhttptest',
	'dos-slowloris',
	'port-scan',
	'ssh-bruteforce',
]

attacks_prettyfied = {
	'active-wiretap': 'Active Wiretap',
	'arp-mitm': 'ARP MitM',
	'dos-syn': 'DoS SYN Flood',
	'fuzzing': 'Fuzzing',
	'os-scan': 'OS Scan',
	'ssdp-flood': 'SSDP Flood',
	'ssl-renegotiation': 'SSL Renegotiation',
	'video-injection': 'Video Injection',
	'botnet': 'Botnet',
	'ddos-hoic': 'DDoS HOIC',
	'ddos-loic': 'DDoS LOIC',
	'dos-goldeneye': 'DoS Goldeneye',
	'dos-hulk': 'DoS Hulk',
	'dos-slowhttptest': 'DoS slowhttptest',
	'dos-slowloris': 'DoS Slowloris',
	'port-scan': 'Port Scan',
	'ssh-bruteforce': 'SSH Bruteforce',
}
