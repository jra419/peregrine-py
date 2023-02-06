#!/usr/bin/env python3

import argparse

from scapy.all import *
from scapy.utils import PcapWriter

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description="Trim packet length to 1500B MTU but keep original IP length value."
	)

	parser.add_argument('--input', help='name of input pcap file', required=True)
	parser.add_argument('--output', help='name of output pcap file', required=True)
	args = parser.parse_args()

	in_pkts = PcapReader(args.input)

	counters = {}

	for pkt in in_pkts:
		length = len(pkt)
		if length not in m:
			counters[length] = 1
		else:
			counters[length] += 1
	
	keys = sorted(list(counters.keys()))
	for length in keys:
		print(f'{length} \t {counters[length]}')

    # pktdump = PcapWriter(args.output, append=False)