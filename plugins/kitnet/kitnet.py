#!/usr/bin/env python

from concurrent import futures

import sys
import os
import time
import struct
import socket
import argparse
import signal
import pickle
import subprocess

from KitNET.KitNET import KitNET

import numpy as np
from pathlib import Path

SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))

DEFAULT_HOST='127.0.0.1'
DEFAULT_PORT=50051
DEFAULT_MAX_AUTOENCODER_SIZE=10
DEFAULT_FM_GRACE_PERIOD=100000
DEFAULT_AD_GRACE_PERIOD=900000
DEFAULT_LEARNING_RATE=0.1
DEFAULT_HIDDEN_RATIO=0.75

MAX_MESSAGE_SIZE = 1500

LAMBDAS=4
FEATURES=80

server = None

class Sample:
	def __init__(self, buffer):
		self.buffer = buffer

		self.mac_src                   = self.parse_buffer(6)
		self.ip_src                    = self.parse_buffer(4)
		self.ip_dst                    = self.parse_buffer(4)
		self.ip_proto                  = self.parse_buffer(1)
		self.port_src                  = self.parse_buffer(2)
		self.port_dst                  = self.parse_buffer(2)
		self.decay                     = self.parse_buffer(4)
		self.mac_ip_src_pkt_cnt        = self.parse_buffer(4)
		self.mac_ip_src_mean           = self.parse_buffer(4)
		self.mac_ip_src_std_dev        = self.parse_buffer(4)
		self.ip_src_pkt_cnt            = self.parse_buffer(4)
		self.ip_src_mean               = self.parse_buffer(4)
		self.ip_src_std_dev            = self.parse_buffer(4)
		self.ip_pkt_cnt                = self.parse_buffer(4)
		self.ip_mean_0                 = self.parse_buffer(4)
		self.ip_std_dev_0              = self.parse_buffer(4)
		self.ip_magnitude              = self.parse_buffer(4)
		self.ip_radius                 = self.parse_buffer(4)
		self.five_t_pkt_cnt            = self.parse_buffer(4)
		self.five_t_mean_0             = self.parse_buffer(4)
		self.five_t_std_dev_0          = self.parse_buffer(4)
		self.five_t_magnitude          = self.parse_buffer(4)
		self.five_t_radius             = self.parse_buffer(4)
		self.ip_sum_res_prod_cov       = self.parse_buffer(8)
		self.ip_pcc                    = self.parse_buffer(8)
		self.five_t_sum_res_prod_cov   = self.parse_buffer(8)
		self.five_t_pcc                = self.parse_buffer(8)
	
	def parse_buffer(self, size_bytes):
		assert self.buffer
		value = 0
		for i in range(size_bytes):
			byte = (self.buffer[i] & 0xff) << (i * 8)
			value |= byte
		self.buffer = self.buffer[size_bytes:]
		return value
	
	def to_array(self):
		return [
			self.mac_src,
			self.ip_src,
			self.ip_dst,
			self.ip_proto,
			self.port_src,
			self.port_dst,
			self.decay,
			self.mac_ip_src_pkt_cnt,
			self.mac_ip_src_mean,
			self.mac_ip_src_std_dev,
			self.ip_src_pkt_cnt,
			self.ip_src_mean,
			self.ip_src_std_dev,
			self.ip_pkt_cnt,
			self.ip_mean_0,
			self.ip_std_dev_0,
			self.ip_magnitude,
			self.ip_radius,
			self.five_t_pkt_cnt,
			self.five_t_mean_0,
			self.five_t_std_dev_0,
			self.five_t_magnitude,
			self.five_t_radius,
			self.ip_sum_res_prod_cov,
			self.ip_pcc,
			self.five_t_sum_res_prod_cov,
			self.five_t_pcc,
		]
	
	def big_to_little_64b(self, v):
		return struct.unpack('>Q', struct.pack('<Q', v))[0]

	def big_to_little_32b(self, v):
		return struct.unpack('>L', struct.pack('<L', v))[0]
	
	def big_to_little_16b(self, v):
		return struct.unpack('>H', struct.pack('<H', v))[0]

	def dump(self):
		print("Sample:")
		print( "  mac_src:                 %02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", self.mac_src.to_bytes(6, 'big')))
		print(f"  ip_src:                  {socket.inet_ntoa(self.ip_src.to_bytes(4, 'little'))}")
		print(f"  ip_dst:                  {socket.inet_ntoa(self.ip_dst.to_bytes(4, 'little'))}")
		print(f"  ip_proto:                {self.ip_proto}")
		print(f"  port_src:                {self.port_src}")
		print(f"  port_dst:                {self.port_dst}")
		print(f"  decay:                   {self.decay}")
		print(f"  mac_ip_src_pkt_cnt:      {self.mac_ip_src_pkt_cnt}")
		print(f"  mac_ip_src_mean:         {self.mac_ip_src_mean}")
		print(f"  mac_ip_src_std_dev:      {self.mac_ip_src_std_dev}")
		print(f"  ip_src_pkt_cnt:          {self.ip_src_pkt_cnt}")
		print(f"  ip_src_mean:             {self.ip_src_mean}")
		print(f"  ip_src_std_dev:          {self.ip_src_std_dev}")
		print(f"  ip_pkt_cnt:              {self.ip_pkt_cnt}")
		print(f"  ip_mean_0:               {self.ip_mean_0}")
		print(f"  ip_std_dev_0:            {self.ip_std_dev_0}")
		print(f"  ip_magnitude:            {self.ip_magnitude}")
		print(f"  ip_radius:               {self.ip_radius}")
		print(f"  five_t_pkt_cnt:          {self.five_t_pkt_cnt}")
		print(f"  five_t_mean_0:           {self.five_t_mean_0}")
		print(f"  five_t_std_dev_0:        {self.five_t_std_dev_0}")
		print(f"  five_t_magnitude:        {self.five_t_magnitude}")
		print(f"  five_t_radius:           {self.five_t_radius}")
		print(f"  ip_sum_res_prod_cov:     {self.ip_sum_res_prod_cov}")
		print(f"  ip_pcc:                  {self.ip_pcc}")
		print(f"  five_t_sum_res_prod_cov: {self.five_t_sum_res_prod_cov}")
		print(f"  five_t_pcc:              {self.five_t_pcc}")

class KitNet():
	def __init__(self, max_autoencoder_size, fm_grace_period, ad_grace_period,
					learning_rate, hidden_ratio,
					feature_map, ensemble_layer, output_layer, train_stats,
					training_out_dir, training_name,
					verbose=False):

		# Initialize KitNET.
		self.AnomDetector = KitNET(FEATURES, max_autoencoder_size, fm_grace_period,
								   ad_grace_period, learning_rate, hidden_ratio,
								   feature_map, ensemble_layer, output_layer,
								   training_out_dir, training_name)

		self.decay_to_pos = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3,
							 8192: 1, 16384: 2, 24576: 3}

		self.fm_grace = fm_grace_period
		self.ad_grace = ad_grace_period
		self.m = max_autoencoder_size

		self.training_out_dir = training_out_dir
		self.training_name = training_name

		# If train_skip is true, import the previously generated models.
		self.train = self.training_out_dir and self.training_name

		self.processed_samples = 0

		if not self.train:
			with open(train_stats, 'rb') as f_stats:
				stats = pickle.load(f_stats)
				self.stats_mac_ip_src = stats[0]
				self.stats_ip_src = stats[1]
				self.stats_ip = stats[2]
				self.stats_five_t = stats[3]
		else:
			self.stats_mac_ip_src = {}
			self.stats_ip_src = {}
			self.stats_ip = {}
			self.stats_five_t = {}
		
		self.verbose = verbose

	def save_stats(self):
		train_stats = [self.stats_mac_ip_src,
					   self.stats_ip_src,
					   self.stats_ip,
					   self.stats_five_t]

		outdir = f'{self.training_out_dir}'

		if not os.path.exists(outdir):
			os.mkdir(outdir)
		
		stats = f'{outdir}/{self.training_name}-m-{self.m}-train-stats.txt'

		with open(stats, 'wb') as f_stats:
			pickle.dump(train_stats, f_stats)

	def reset_stats(self):
		print('Reset stats')

		self.stats_mac_ip_src = {}
		self.stats_ip_src = {}
		self.stats_ip = {}
		self.stats_five_t = {}

	def ProcessSample(self, sample):
		if self.verbose:
			sample.dump()
		
		sample_array = sample.to_array()

		cur_decay_pos = self.decay_to_pos[sample_array[6]]

		hdr_mac_ip_src = f'{sample_array[0]}{sample_array[1]}'
		hdr_ip_src     = f'{sample_array[1]}'
		hdr_ip         = f'{sample_array[1]}{sample_array[2]}'
		hdr_five_t     = f'{sample_array[1]}{sample_array[2]}{sample_array[3]}{sample_array[4]}{sample_array[5]}'

		if hdr_mac_ip_src not in self.stats_mac_ip_src:
			self.stats_mac_ip_src[hdr_mac_ip_src] = np.zeros(3 * LAMBDAS)

		self.stats_mac_ip_src[hdr_mac_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = sample_array[7:10]

		if hdr_ip_src not in self.stats_ip_src:
			self.stats_ip_src[hdr_ip_src] = np.zeros(3 * LAMBDAS)
	
		self.stats_ip_src[hdr_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = sample_array[10:13]

		if hdr_ip not in self.stats_ip:
			self.stats_ip[hdr_ip] = np.zeros(7 * LAMBDAS)
		
		self.stats_ip[hdr_ip][(7*cur_decay_pos):(7*cur_decay_pos+7)] = sample_array[13:20]

		if hdr_five_t not in self.stats_five_t:
			self.stats_five_t[hdr_five_t] = np.zeros(7 * LAMBDAS)

		self.stats_five_t[hdr_five_t][(7*cur_decay_pos):(7*cur_decay_pos+7)] = sample_array[20:]

		processed_stats = np.concatenate((self.stats_mac_ip_src[hdr_mac_ip_src],
										  self.stats_ip_src[hdr_ip_src],
										  self.stats_ip[hdr_ip],
										  self.stats_five_t[hdr_five_t]))	

		# Convert any existing NaNs to 0.
		processed_stats[np.isnan(processed_stats)] = 0

		# Run KitNET with the current statistics.
		rmse = self.AnomDetector.process(processed_stats)
		self.processed_samples += 1

		if self.train and self.processed_samples == self.fm_grace + self.ad_grace:
			self.save_stats()

		if self.verbose:
			print(f'rmse: {rmse}')

		return rmse

def serve(kitnet, host=DEFAULT_HOST, port=DEFAULT_PORT, verbose=False):
	global server
	
	server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	server_socket.bind((host, port))

	print(f"Listening on {port}...", flush=True)

	while True:
		msg, client = server_socket.recvfrom(MAX_MESSAGE_SIZE)
		sample = Sample(msg)
		rmse = kitnet.ProcessSample(sample)
		server_socket.sendto(struct.pack("f", rmse), client)

def handle_sigterm(*args):
	print('Done.')
	exit(0)

def print_header():
	print()
	print("*******************************************")
	print("*                                         *")
	print("*        PEREGRINE KITNET PLUGIN          *")
	print("*                                         *")
	print("*******************************************")
	print()

if __name__ == '__main__':
	signal.signal(signal.SIGINT, handle_sigterm)

	parser = argparse.ArgumentParser(description='Peregrine-KitNet ML model plugin')
	
	parser.add_argument('--verbose',
		action='store_true',
		help='verbose mode')
	
	parser.add_argument('--max_autoencoder_size',
		type=int,
		default=DEFAULT_MAX_AUTOENCODER_SIZE,
		help='m value')

	parser.add_argument('--fm_grace_period',
		type=int,
		default=DEFAULT_FM_GRACE_PERIOD,
		help='Feature mapper grace period')

	parser.add_argument('--ad_grace_period',
		type=int,
		default=DEFAULT_AD_GRACE_PERIOD,
		help='Anomaly detector grace period')

	parser.add_argument('--learning_rate',
		type=float,
		default=DEFAULT_LEARNING_RATE,
		help='Learning rate')

	parser.add_argument('--hidden_ratio',
		type=float,
		default=DEFAULT_HIDDEN_RATIO,
		help='Hidden ratio')

	parser.add_argument('--feature_map',
		type=str,
		default=None,
		help='Path of feature mapper input file')

	parser.add_argument('--ensemble_layer',
		type=str,
		default=None,
		help='Path of ensemble layer input file')

	parser.add_argument('--output_layer',
		type=str,
		default=None,
		help='Path of output layer input file')

	parser.add_argument('--train_stats',
		type=str,
		default=None,
		help='Path of training statistics input file')

	parser.add_argument('--training_out_dir',
		type=str,
		default=None,
		help='Path for output training data files')

	parser.add_argument('--training_name',
		type=str,
		default=None,
		help='Prefix name of training output data files')

	args = parser.parse_args()

	use_training_data = args.feature_map or args.ensemble_layer or args.output_layer or args.train_stats
	has_all_training_data = args.feature_map and args.ensemble_layer and args.output_layer and args.train_stats
	has_all_training_output_data = args.training_out_dir and args.training_name

	if use_training_data and not has_all_training_data:
		print('Error: incomplete training data provided. Exiting.')
		exit(1)
	
	if not use_training_data and not has_all_training_output_data:
		print('Error: incomplete output training data provided. Exiting.')
		exit(1)
	
	print_header()

	kitnet = KitNet(
		max_autoencoder_size=args.max_autoencoder_size,
		fm_grace_period=args.fm_grace_period,
		ad_grace_period=args.ad_grace_period,
		learning_rate=args.learning_rate,
		hidden_ratio=args.hidden_ratio,
		feature_map=args.feature_map,
		ensemble_layer=args.ensemble_layer,
		output_layer=args.output_layer,
		train_stats=args.train_stats,
		training_out_dir=args.training_out_dir,
		training_name=args.training_name,
		verbose=args.verbose
	)

	serve(kitnet, verbose=args.verbose)