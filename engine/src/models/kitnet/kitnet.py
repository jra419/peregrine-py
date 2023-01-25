#!/usr/bin/python3

from concurrent import futures

import grpc
import sys
import os
import time
import struct
import socket
import argparse
import signal

SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))
GRPC_AUTOGEN_SOURCES_PATH=f"{SCRIPT_DIR}/../../../autogen"
sys.path.append(GRPC_AUTOGEN_SOURCES_PATH)

import kitnet_pb2
import kitnet_pb2_grpc

DEFAULT_GRPC_PORT=50051
server = None

class Sample:
	def __init__(self, process_sample_request):
		self.mac_src = process_sample_request.mac_src.to_bytes(6, 'big')
		self.ip_src = process_sample_request.ip_src
		self.ip_dst = process_sample_request.ip_dst & 0xffffffff
		self.ip_proto = process_sample_request.ip_proto & 0xff
		self.port_src = process_sample_request.port_src & 0xffff
		self.port_dst = process_sample_request.port_dst & 0xffff
		self.decay = process_sample_request.decay
		self.mac_ip_src_pkt_cnt = process_sample_request.mac_ip_src_pkt_cnt
		self.mac_ip_src_mean = process_sample_request.mac_ip_src_mean
		self.mac_ip_src_std_dev = process_sample_request.mac_ip_src_std_dev
		self.ip_src_pkt_cnt = process_sample_request.ip_src_pkt_cnt
		self.ip_src_mean = process_sample_request.ip_src_mean
		self.ip_src_std_dev = process_sample_request.ip_src_std_dev
		self.ip_pkt_cnt = process_sample_request.ip_pkt_cnt
		self.ip_mean_0 = process_sample_request.ip_mean_0
		self.ip_std_dev_0 = process_sample_request.ip_std_dev_0
		self.ip_magnitude = process_sample_request.ip_magnitude
		self.ip_radius = process_sample_request.ip_radius
		self.five_t_pkt_cnt = process_sample_request.five_t_pkt_cnt
		self.five_t_mean_0 = process_sample_request.five_t_mean_0
		self.five_t_std_dev_0 = process_sample_request.five_t_std_dev_0
		self.five_t_magnitude = process_sample_request.five_t_magnitude
		self.five_t_radius = process_sample_request.five_t_radius
		self.ip_sum_res_prod_cov = process_sample_request.ip_sum_res_prod_cov
		self.ip_pcc = process_sample_request.ip_pcc
		self.five_t_sum_res_prod_cov = process_sample_request.five_t_sum_res_prod_cov
		self.five_t_pcc = process_sample_request.five_t_pcc
	
	def big_to_little_64b(self, v):
		return struct.unpack('>Q', struct.pack('<Q', v))[0]

	def big_to_little_32b(self, v):
		return struct.unpack('>L', struct.pack('<L', v))[0]
	
	def big_to_little_16b(self, v):
		return struct.unpack('>H', struct.pack('<H', v))[0]

	def dump(self):
		print("Sample:")
		print( "  mac_src:                 %02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", self.mac_src))
		print(f"  ip_src:                  {socket.inet_ntoa(struct.pack('<L', self.ip_src))}")
		print(f"  ip_dst:                  {socket.inet_ntoa(struct.pack('<L', self.ip_dst))}")
		print(f"  ip_proto:                {self.ip_proto}")
		print(f"  port_src:                {self.big_to_little_16b(self.port_src)}")
		print(f"  port_dst:                {self.big_to_little_16b(self.port_dst)}")
		print(f"  decay:                   {self.big_to_little_32b(self.decay)}")
		print(f"  mac_ip_src_pkt_cnt:      {self.big_to_little_32b(self.mac_ip_src_pkt_cnt)}")
		print(f"  mac_ip_src_mean:         {self.big_to_little_32b(self.mac_ip_src_mean)}")
		print(f"  mac_ip_src_std_dev:      {self.big_to_little_32b(self.mac_ip_src_std_dev)}")
		print(f"  ip_src_pkt_cnt:          {self.big_to_little_32b(self.ip_src_pkt_cnt)}")
		print(f"  ip_src_mean:             {self.big_to_little_32b(self.ip_src_mean)}")
		print(f"  ip_src_std_dev:          {self.big_to_little_32b(self.ip_src_std_dev)}")
		print(f"  ip_pkt_cnt:              {self.big_to_little_32b(self.ip_pkt_cnt)}")
		print(f"  ip_mean_0:               {self.big_to_little_32b(self.ip_mean_0)}")
		print(f"  ip_std_dev_0:            {self.big_to_little_32b(self.ip_std_dev_0)}")
		print(f"  ip_magnitude:            {self.big_to_little_32b(self.ip_magnitude)}")
		print(f"  ip_radius:               {self.big_to_little_32b(self.ip_radius)}")
		print(f"  five_t_pkt_cnt:          {self.big_to_little_32b(self.five_t_pkt_cnt)}")
		print(f"  five_t_mean_0:           {self.big_to_little_32b(self.five_t_mean_0)}")
		print(f"  five_t_std_dev_0:        {self.big_to_little_32b(self.five_t_std_dev_0)}")
		print(f"  five_t_magnitude:        {self.big_to_little_32b(self.five_t_magnitude)}")
		print(f"  five_t_radius:           {self.big_to_little_32b(self.five_t_radius)}")
		print(f"  ip_sum_res_prod_cov:     {self.big_to_little_64b(self.ip_sum_res_prod_cov)}")
		print(f"  ip_pcc:                  {self.big_to_little_64b(self.ip_pcc)}")
		print(f"  five_t_sum_res_prod_cov: {self.big_to_little_64b(self.five_t_sum_res_prod_cov)}")
		print(f"  five_t_pcc:              {self.big_to_little_64b(self.five_t_pcc)}")

class KitNet(kitnet_pb2_grpc.KitNetServicer):
	def __init__(self, verbose=False):
		self.verbose = verbose

	def ProcessSample(self, request, context):
		sample = Sample(request)

		if self.verbose:
			sample.dump()

		rmse = 0.1
		return kitnet_pb2.ProcessSampleReply(RMSE=rmse)

def serve(port=DEFAULT_GRPC_PORT, verbose=False):
	global server
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	kitnet_pb2_grpc.add_KitNetServicer_to_server(KitNet(verbose), server)
	server.add_insecure_port(f'[::]:{port}')
	server.start()

	print(f"Listening on {port}...")

def handle_sigterm(*args):
	global server
	
	print('\nStopping...')

	done_event = server.stop(30)
	done_event.wait(30)

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
	parser = argparse.ArgumentParser(description='Peregrine-KitNet ML model plugin')

	parser.add_argument('-p', '--port', \
		type=int,                       \
		default=DEFAULT_GRPC_PORT,      \
		help='gRPC serving port')
	
	parser.add_argument('--verbose',    \
		action='store_true',            \
		help='verbose mode')

	args = parser.parse_args()
	
	print_header()
	serve(port=args.port, verbose=args.verbose)
	signal.signal(signal.SIGINT, handle_sigterm)

	while True:
		time.sleep(5)