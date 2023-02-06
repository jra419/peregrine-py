#!/usr/bin/env python3

import argparse
import subprocess

from scapy.all import *
from scapy.utils import PcapWriter

MTU = 1500

def get_packets_in_pcap(pcap):
	cmd = [ 'capinfos', '-c', '-M', pcap ]
	proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	out = proc.stdout.decode('utf-8')
	err = proc.stderr.decode('utf-8')

	if proc.returncode != 0:
		print(err)
		exit(1)
	
	lines = out.split('\n')
	assert len(lines) >= 2

	nr_pkts = lines[1]
	nr_pkts = nr_pkts.split(' ')[-1]
	nr_pkts = int(nr_pkts)
	
	return nr_pkts

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description=f"Trim packet length to {MTU}B MTU but keep original IP length value."
	)

	parser.add_argument('--input', help='name of input pcap file', required=True)
	parser.add_argument('--output', help='name of output pcap file', required=True)
	args = parser.parse_args()

	in_pkts   = PcapReader(args.input)
	pktdump   = PcapWriter(args.output, append=False)
	n_pkts    = get_packets_in_pcap(args.input)
	processed = 0

	for pkt in in_pkts:
		processed += 1
		print(f'Progress: {int(100.0 * processed / n_pkts)}%', end='\r')

		length = len(pkt)
		
		if Ether not in pkt and length > MTU:
			print("Not ethernet but bigger than MTU:")
			print(pkt)
			exit(1)

		if length <= MTU:
			out_pkt = pkt
		else:
			l2 = pkt[Ether]
			l3 = l2.payload
			l4 = l3.payload

			l2.remove_payload()
			l3.remove_payload()
			l4.remove_payload()

			payload = (MTU - (len(l2) + len(l3) + len(l4))) * 'A'
			out_pkt = l2 / l3 / l4 / payload

		pktdump.write(out_pkt)
	print()
