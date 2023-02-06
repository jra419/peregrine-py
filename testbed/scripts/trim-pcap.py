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

		if Ether not in pkt:
			continue
		
		length = len(pkt) - ETHERNET_SIZE

		if length > MTU:
			payload = pkt.lastlayer()
			base    = length - len(payload)
			payload.load = (MTU - (base + PEREGRINE_HDR_SIZE)) * 'A'
			
			if   TCP  in pkt: pkt[TCP].chksum  = 0
			elif UDP  in pkt: pkt[UDP].chksum  = 0
			elif ICMP in pkt: pkt[ICMP].chksum = 0
			else: continue
		else: continue # FIXME: remove

		out_pkt = pkt
		pktdump.write(out_pkt)

	print()
