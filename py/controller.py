#!/usr/bin/env python3

import os
import sys
import signal
import logging
import argparse
import json
import ptf.testutils as testutils
from ptf import config
import random
# add BF Python to search path
try:
    # Import BFRT GRPC stuff
    import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
    import bfrt_grpc.client as gc
    import grpc
except:
    sys.path.append(os.environ['SDE_INSTALL'] + '/lib/python3.7/site-packages/tofino')
    import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
    import bfrt_grpc.client as gc
    import grpc

from ports import Ports
from peregrine_tables import FwdRecirculation_a, FwdRecirculation_b, Fwd_a, Fwd_b
from peregrine_tables import MacSrcIpSrcPktMean, IpSrcPktMean
from peregrine_tables import IpPktMean, IpCov, IpStdDevProd, IpPcc, FiveTPktMean, FiveTCov, FiveTStdDevProd, FiveTPcc

logger = None
grpc_client = None


def make_port(pipe, local_port):
    """ Given a pipe and a port within that pipe construct the full port number. """
    return (pipe << 7) | local_port


def port_to_local_port(port):
    """ Given a port return its ID within a pipe. """
    print('actual port', port)
    local_port = port & 0x7F
    print('local port', local_port)
    assert (local_port < 72)
    return local_port


def port_to_pipe(port):
    """ Given a port return the pipe it belongs to. """
    local_port = port_to_local_port(port)
    pipe = (port >> 7) & 0x3
    assert (port == make_port(pipe, local_port))
    return pipe


def get_internal_port_from_external(ext_port, internal_pipes, external_pipes):
    pipe_local_port = port_to_local_port(ext_port)
    int_pipe = internal_pipes[external_pipes.index(port_to_pipe(ext_port))]

    # For Tofino-1 we are currently using a 1-to-1 mapping from external port to internal port so just replace the pipe-id.
    return make_port(int_pipe, pipe_local_port)


def get_port_from_pipes(pipes, swports_by_pipe):
    ports = list()
    for pipe in pipes:
        ports = ports + swports_by_pipe[pipe]
    print('ports', ports)
    return random.choice(ports)


def setup_grpc_client(server, port, program):
    global grpc_client

    # connect to GRPC server
    logger.info("Connecting to GRPC server {}:{} and binding to program {}...".format(args.grpc_server,
                                                                                      args.grpc_port,
                                                                                      args.program))
    grpc_client = gc.ClientInterface("{}:{}".format(args.grpc_server, args.grpc_port), 0, 0)
    grpc_client.bind_pipeline_config(args.program)


def configure_switch(program, topology):
    # get all tables for program
    bfrt_info = grpc_client.bfrt_info_get(program)
    # print(bfrt_info)

    # setup ports
    Ports.ports = Ports(gc, bfrt_info)

    print('topology ports', topology['ports'])
    for entry in topology['ports']:
        Ports.ports.add_port(entry['port'], 0, entry['capacity'], 'none')

    # available_ports = Ports.ports.get_available_ports()
    # print(available_ports)

    # Setup pipes
    # print('num_pipes', testutils.test_param_get('num_pipes'))
    # num_pipes = int(testutils.test_param_get('num_pipes'))
    num_pipes = 4
    pipes = list(range(num_pipes))

    swports = []
    swports_by_pipe = {p: list() for p in pipes}
    print(config)
    ports = [5, 6, 10, 11, 29, 30, 31, 32]
    for port in ports:
        swports.append(port)
        swports.sort()
        for port in swports:
            pipe = port_to_pipe(port)
            swports_by_pipe[pipe].append(port)
    # for device, port, ifname in config["interfaces"]:
        # swports.append(port)
        # swports.sort()
        # for port in swports:
            # pipe = port_to_pipe(port)
            # swports_by_pipe[pipe].append(port)

    # Tofino-1 uses pipes 0 and 2 as the external pipes while 1 and 3 are the internal pipes.
    external_pipes = [0, 2]
    internal_pipes = [1, 3]

    print('external pipes ', external_pipes)
    ig_port = get_port_from_pipes(external_pipes, swports_by_pipe)
    print('ig_port ', ig_port)
    eg_port = get_port_from_pipes(external_pipes, swports_by_pipe)
    print('eg_port ', eg_port)

    int_port = get_internal_port_from_external(ig_port, internal_pipes, external_pipes)
    print('int_port ', int_port)
    logger.info("Expected forwarding path:")
    logger.info(" 1. Ingress processing in external pipe %d, ingress port %d", port_to_pipe(ig_port), ig_port)
    logger.info(" 2. Egress processing in internal pipe %d, internal port %d", port_to_pipe(int_port), int_port)
    logger.info(" 3. Loopback on internal port %d", int_port)
    logger.info(" 4. Ingress processing in internal pipe %d, internal port %d", port_to_pipe(int_port), int_port)
    logger.info(" 5. Egress processing in external pipe %d, egress port %d", port_to_pipe(eg_port), eg_port)

    # Setup tables

    a_fwd_recirculation = FwdRecirculation_a(gc, bfrt_info)
    b_fwd_recirculation = FwdRecirculation_b(gc, bfrt_info)
    a_fwd = Fwd_a(gc, bfrt_info)
    b_fwd = Fwd_b(gc, bfrt_info)
    mac_src_ip_src_pkt_mean = MacSrcIpSrcPktMean(gc, bfrt_info)
    ip_src_pkt_mean = IpSrcPktMean(gc, bfrt_info)
    ip_pkt_mean = IpPktMean(gc, bfrt_info)
    ip_cov = IpCov(gc, bfrt_info)
    ip_std_dev_prod = IpStdDevProd(gc, bfrt_info)
    ip_pcc = IpPcc(gc, bfrt_info)
    five_t_pkt_mean = FiveTPktMean(gc, bfrt_info)
    five_t_cov = FiveTCov(gc, bfrt_info)
    five_t_std_dev_prod = FiveTStdDevProd(gc, bfrt_info)
    five_t_pcc = FiveTPcc(gc, bfrt_info)

    a_fwd_recirculation.add_entry(ig_port, int_port)
    b_fwd_recirculation.add_entry(ig_port, eg_port)
    a_fwd.add_entry('5.6.7.8', 63)
    b_fwd.add_entry('5.6.7.8', 64)

    mac_src_ip_src_pkt_mean.add_entry(15, 2, 0b11111110, 1)
    mac_src_ip_src_pkt_mean.add_entry(14, 4, 0b11111100, 2)
    mac_src_ip_src_pkt_mean.add_entry(13, 8, 0b11111000, 3)
    mac_src_ip_src_pkt_mean.add_entry(12, 16, 0b11110000, 4)
    mac_src_ip_src_pkt_mean.add_entry(11, 32, 0b11100000, 5)
    mac_src_ip_src_pkt_mean.add_entry(10, 64, 0b11000000, 6)
    mac_src_ip_src_pkt_mean.add_entry(9, 128, 0b10000000, 7)
    mac_src_ip_src_pkt_mean.add_entry(8, 256, 0b1111111100000000, 8)
    mac_src_ip_src_pkt_mean.add_entry(7, 512, 0b1111111000000000, 9)
    mac_src_ip_src_pkt_mean.add_entry(6, 1024, 0b1111110000000000, 10)
    mac_src_ip_src_pkt_mean.add_entry(5, 2048, 0b1111100000000000, 11)
    mac_src_ip_src_pkt_mean.add_entry(4, 4096, 0b1111000000000000, 12)
    mac_src_ip_src_pkt_mean.add_entry(3, 8192, 0b1110000000000000, 13)
    mac_src_ip_src_pkt_mean.add_entry(2, 16384, 0b1100000000000000, 14)
    mac_src_ip_src_pkt_mean.add_entry(1, 32768, 0b1000000000000000, 15)

    ip_src_pkt_mean.add_entry(15, 2, 0b11111110, 1)
    ip_src_pkt_mean.add_entry(14, 4, 0b11111100, 2)
    ip_src_pkt_mean.add_entry(13, 8, 0b11111000, 3)
    ip_src_pkt_mean.add_entry(12, 16, 0b11110000, 4)
    ip_src_pkt_mean.add_entry(11, 32, 0b11100000, 5)
    ip_src_pkt_mean.add_entry(10, 64, 0b11000000, 6)
    ip_src_pkt_mean.add_entry(9, 128, 0b10000000, 7)
    ip_src_pkt_mean.add_entry(8, 256, 0b1111111100000000, 8)
    ip_src_pkt_mean.add_entry(7, 512, 0b1111111000000000, 9)
    ip_src_pkt_mean.add_entry(6, 1024, 0b1111110000000000, 10)
    ip_src_pkt_mean.add_entry(5, 2048, 0b1111100000000000, 11)
    ip_src_pkt_mean.add_entry(4, 4096, 0b1111000000000000, 12)
    ip_src_pkt_mean.add_entry(3, 8192, 0b1110000000000000, 13)
    ip_src_pkt_mean.add_entry(2, 16384, 0b1100000000000000, 14)
    ip_src_pkt_mean.add_entry(1, 32768, 0b1000000000000000, 15)

    ip_pkt_mean.add_entry(15, 2, 0b11111110, 1)
    ip_pkt_mean.add_entry(14, 4, 0b11111100, 2)
    ip_pkt_mean.add_entry(13, 8, 0b11111000, 3)
    ip_pkt_mean.add_entry(12, 16, 0b11110000, 4)
    ip_pkt_mean.add_entry(11, 32, 0b11100000, 5)
    ip_pkt_mean.add_entry(10, 64, 0b11000000, 6)
    ip_pkt_mean.add_entry(9, 128, 0b10000000, 7)
    ip_pkt_mean.add_entry(8, 256, 0b1111111100000000, 8)
    ip_pkt_mean.add_entry(7, 512, 0b1111111000000000, 9)
    ip_pkt_mean.add_entry(6, 1024, 0b1111110000000000, 10)
    ip_pkt_mean.add_entry(5, 2048, 0b1111100000000000, 11)
    ip_pkt_mean.add_entry(4, 4096, 0b1111000000000000, 12)
    ip_pkt_mean.add_entry(3, 8192, 0b1110000000000000, 13)
    ip_pkt_mean.add_entry(2, 16384, 0b1100000000000000, 14)
    ip_pkt_mean.add_entry(1, 32768, 0b1000000000000000, 15)

    ip_cov.add_entry(15, 2, 0b11111110, 1)
    ip_cov.add_entry(14, 4, 0b11111100, 2)
    ip_cov.add_entry(13, 8, 0b11111000, 3)
    ip_cov.add_entry(12, 16, 0b11110000, 4)
    ip_cov.add_entry(11, 32, 0b11100000, 5)
    ip_cov.add_entry(10, 64, 0b11000000, 6)
    ip_cov.add_entry(9, 128, 0b10000000, 7)
    ip_cov.add_entry(8, 256, 0b1111111100000000, 8)
    ip_cov.add_entry(7, 512, 0b1111111000000000, 9)
    ip_cov.add_entry(6, 1024, 0b1111110000000000, 10)
    ip_cov.add_entry(5, 2048, 0b1111100000000000, 11)
    ip_cov.add_entry(4, 4096, 0b1111000000000000, 12)
    ip_cov.add_entry(3, 8192, 0b1110000000000000, 13)
    ip_cov.add_entry(2, 16384, 0b1100000000000000, 14)
    ip_cov.add_entry(1, 32768, 0b1000000000000000, 15)

    ip_std_dev_prod.add_entry(15, 2, 0b11111110, 1)
    ip_std_dev_prod.add_entry(14, 4, 0b11111100, 2)
    ip_std_dev_prod.add_entry(13, 8, 0b11111000, 3)
    ip_std_dev_prod.add_entry(12, 16, 0b11110000, 4)
    ip_std_dev_prod.add_entry(11, 32, 0b11100000, 5)
    ip_std_dev_prod.add_entry(10, 64, 0b11000000, 6)
    ip_std_dev_prod.add_entry(9, 128, 0b10000000, 7)
    ip_std_dev_prod.add_entry(8, 256, 0b1111111100000000, 8)
    ip_std_dev_prod.add_entry(7, 512, 0b1111111000000000, 9)
    ip_std_dev_prod.add_entry(6, 1024, 0b1111110000000000, 10)
    ip_std_dev_prod.add_entry(5, 2048, 0b1111100000000000, 11)
    ip_std_dev_prod.add_entry(4, 4096, 0b1111000000000000, 12)
    ip_std_dev_prod.add_entry(3, 8192, 0b1110000000000000, 13)
    ip_std_dev_prod.add_entry(2, 16384, 0b1100000000000000, 14)
    ip_std_dev_prod.add_entry(1, 32768, 0b1000000000000000, 15)

    ip_pcc.add_entry(15, 2, 0b11111110, 1)
    ip_pcc.add_entry(14, 4, 0b11111100, 2)
    ip_pcc.add_entry(13, 8, 0b11111000, 3)
    ip_pcc.add_entry(12, 16, 0b11110000, 4)
    ip_pcc.add_entry(11, 32, 0b11100000, 5)
    ip_pcc.add_entry(10, 64, 0b11000000, 6)
    ip_pcc.add_entry(9, 128, 0b10000000, 7)
    ip_pcc.add_entry(8, 256, 0b1111111100000000, 8)
    ip_pcc.add_entry(7, 512, 0b1111111000000000, 9)
    ip_pcc.add_entry(6, 1024, 0b1111110000000000, 10)
    ip_pcc.add_entry(5, 2048, 0b1111100000000000, 11)
    ip_pcc.add_entry(4, 4096, 0b1111000000000000, 12)
    ip_pcc.add_entry(3, 8192, 0b1110000000000000, 13)
    ip_pcc.add_entry(2, 16384, 0b1100000000000000, 14)
    ip_pcc.add_entry(1, 32768, 0b1000000000000000, 15)

    five_t_pkt_mean.add_entry(15, 2, 0b11111110, 1)
    five_t_pkt_mean.add_entry(14, 4, 0b11111100, 2)
    five_t_pkt_mean.add_entry(13, 8, 0b11111000, 3)
    five_t_pkt_mean.add_entry(12, 16, 0b11110000, 4)
    five_t_pkt_mean.add_entry(11, 32, 0b11100000, 5)
    five_t_pkt_mean.add_entry(10, 64, 0b11000000, 6)
    five_t_pkt_mean.add_entry(9, 128, 0b10000000, 7)
    five_t_pkt_mean.add_entry(8, 256, 0b1111111100000000, 8)
    five_t_pkt_mean.add_entry(7, 512, 0b1111111000000000, 9)
    five_t_pkt_mean.add_entry(6, 1024, 0b1111110000000000, 10)
    five_t_pkt_mean.add_entry(5, 2048, 0b1111100000000000, 11)
    five_t_pkt_mean.add_entry(4, 4096, 0b1111000000000000, 12)
    five_t_pkt_mean.add_entry(3, 8192, 0b1110000000000000, 13)
    five_t_pkt_mean.add_entry(2, 16384, 0b1100000000000000, 14)
    five_t_pkt_mean.add_entry(1, 32768, 0b1000000000000000, 15)

    five_t_cov.add_entry(15, 2, 0b11111110, 1)
    five_t_cov.add_entry(14, 4, 0b11111100, 2)
    five_t_cov.add_entry(13, 8, 0b11111000, 3)
    five_t_cov.add_entry(12, 16, 0b11110000, 4)
    five_t_cov.add_entry(11, 32, 0b11100000, 5)
    five_t_cov.add_entry(10, 64, 0b11000000, 6)
    five_t_cov.add_entry(9, 128, 0b10000000, 7)
    five_t_cov.add_entry(8, 256, 0b1111111100000000, 8)
    five_t_cov.add_entry(7, 512, 0b1111111000000000, 9)
    five_t_cov.add_entry(6, 1024, 0b1111110000000000, 10)
    five_t_cov.add_entry(5, 2048, 0b1111100000000000, 11)
    five_t_cov.add_entry(4, 4096, 0b1111000000000000, 12)
    five_t_cov.add_entry(3, 8192, 0b1110000000000000, 13)
    five_t_cov.add_entry(2, 16384, 0b1100000000000000, 14)
    five_t_cov.add_entry(1, 32768, 0b1000000000000000, 15)

    five_t_std_dev_prod.add_entry(15, 2, 0b11111110, 1)
    five_t_std_dev_prod.add_entry(14, 4, 0b11111100, 2)
    five_t_std_dev_prod.add_entry(13, 8, 0b11111000, 3)
    five_t_std_dev_prod.add_entry(12, 16, 0b11110000, 4)
    five_t_std_dev_prod.add_entry(11, 32, 0b11100000, 5)
    five_t_std_dev_prod.add_entry(10, 64, 0b11000000, 6)
    five_t_std_dev_prod.add_entry(9, 128, 0b10000000, 7)
    five_t_std_dev_prod.add_entry(8, 256, 0b1111111100000000, 8)
    five_t_std_dev_prod.add_entry(7, 512, 0b1111111000000000, 9)
    five_t_std_dev_prod.add_entry(6, 1024, 0b1111110000000000, 10)
    five_t_std_dev_prod.add_entry(5, 2048, 0b1111100000000000, 11)
    five_t_std_dev_prod.add_entry(4, 4096, 0b1111000000000000, 12)
    five_t_std_dev_prod.add_entry(3, 8192, 0b1110000000000000, 13)
    five_t_std_dev_prod.add_entry(2, 16384, 0b1100000000000000, 14)
    five_t_std_dev_prod.add_entry(1, 32768, 0b1000000000000000, 15)

    five_t_pcc.add_entry(15, 2, 0b11111110, 1)
    five_t_pcc.add_entry(14, 4, 0b11111100, 2)
    five_t_pcc.add_entry(13, 8, 0b11111000, 3)
    five_t_pcc.add_entry(12, 16, 0b11110000, 4)
    five_t_pcc.add_entry(11, 32, 0b11100000, 5)
    five_t_pcc.add_entry(10, 64, 0b11000000, 6)
    five_t_pcc.add_entry(9, 128, 0b10000000, 7)
    five_t_pcc.add_entry(8, 256, 0b1111111100000000, 8)
    five_t_pcc.add_entry(7, 512, 0b1111111000000000, 9)
    five_t_pcc.add_entry(6, 1024, 0b1111110000000000, 10)
    five_t_pcc.add_entry(5, 2048, 0b1111100000000000, 11)
    five_t_pcc.add_entry(4, 4096, 0b1111000000000000, 12)
    five_t_pcc.add_entry(3, 8192, 0b1110000000000000, 13)
    five_t_pcc.add_entry(2, 16384, 0b1100000000000000, 14)
    five_t_pcc.add_entry(1, 32768, 0b1000000000000000, 15)

    # Done with configuration
    logger.info("Switch configured successfully!")


def get_topology(topology_file):
    with open(topology_file, "r") as f:
        data = f.read()
        topology = json.loads(data)
        return topology


if __name__ == "__main__":
    # set up options
    argparser = argparse.ArgumentParser(description="Peregrine controller.")
    argparser.add_argument('--grpc_server', type=str, default='localhost', help='GRPC server name/address')
    argparser.add_argument('--grpc_port', type=int, default=50052, help='GRPC server port')
    argparser.add_argument('--program', type=str, default='peregrine', help='P4 program name')
    argparser.add_argument('--topology', type=str, default='topology.json', help='Topology')
    args = argparser.parse_args()

    # configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(args.program)

    topology = get_topology(args.topology)
    setup_grpc_client(args.grpc_server, args.grpc_port, args.program)
    configure_switch(args.program, topology)

    # exit (bug workaround)
    logger.info("Exiting!")

    # flush logs, stdout, stderr
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()

    # exit (bug workaround)
    os.kill(os.getpid(), signal.SIGTERM)
