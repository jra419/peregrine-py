#!/usr/bin/env python3

import argparse
import subprocess

from scapy.all import *
from scapy.utils import PcapWriter

PEREGRINE_HDR_SIZE = 148
ETHERNET_SIZE = 14
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

	for line in lines:
		if 'Number of packets' not in line:
			continue
		
		nr_pkts = line.split(' ')[-1]
		nr_pkts = int(nr_pkts)
		
		return nr_pkts
	
	assert False and "Line with number of packets not found."

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

		l2 = pkt
		l3 = l2.payload
		l4 = l3.payload

		valid = True
		valid &= Ether in l2
		valid &= IP in l3
		valid &= TCP in l4 or UDP in l4 or ICMP in l4

		if not valid: continue
		
		length         = len(pkt) - ETHERNET_SIZE
		payload_length = len(l4.payload)

		if length + PEREGRINE_HDR_SIZE > MTU:
			base           = length - payload_length
			payload_length = (MTU - (base + PEREGRINE_HDR_SIZE))

		l3.chksum = 0
		l4.chksum = 0

		l2.remove_payload()
		l3.remove_payload()
		l4.remove_payload()

		out_pkt = l2 / l3 / l4 / Raw(payload_length * 'z')

		print(f'Progress: {int(100.0 * processed / n_pkts)}%', end='\r')

		if len(out_pkt) > MTU + PEREGRINE_HDR_SIZE:
			pkt.show2()

			print('Length', len(pkt))
			print('L4 payload lenght', len(l4.payload))
			print('L4 payload', l4.payload)
			exit(1)

		pktdump.write(out_pkt)

	print()
