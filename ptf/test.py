import logging
import random

from ptf import config
from ptf.thriftutils import *
import ptf.testutils as testutils
from bfruntime_client_base_tests import BfRuntimeTest
import bfrt_grpc.client as gc

logger = logging.getLogger('Test')
if not len(logger.handlers):
    logger.addHandler(logging.StreamHandler())


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


num_pipes = int(testutils.test_param_get('num_pipes'))
pipes = list(range(num_pipes))

swports = []
swports_by_pipe = {p: list() for p in pipes}
for device, port, ifname in config["interfaces"]:
    swports.append(port)
swports.sort()
for port in swports:
    pipe = port_to_pipe(port)
    swports_by_pipe[pipe].append(port)


# Tofino-1 uses pipes 0 and 2 as the external pipes while 1 and 3 are the internal pipes.
# Tofino-2 uses pipes 0 and 1 as the external pipes while 2 and 3 are the internal pipes.
arch = testutils.test_param_get('arch')
if arch == "tofino":
    external_pipes = [0, 2]
    internal_pipes = [1, 3]
elif arch == "tofino2":
    external_pipes = [0, 1]
    internal_pipes = [2, 3]
else:
    assert (arch == "tofino" or arch == "tofino2")


def get_internal_port_from_external(ext_port):
    pipe_local_port = port_to_local_port(ext_port)
    int_pipe = internal_pipes[external_pipes.index(port_to_pipe(ext_port))]

    if arch == "tofino":
        # For Tofino-1 we are currently using a 1-to-1 mapping from external
        # port to internal port so just replace the pipe-id.
        return make_port(int_pipe, pipe_local_port)
    elif arch == "tofino2":
        # For Tofino-2 we are currently using internal ports in 400g mode so up
        # to eight external ports (if maximum break out is configured) can map
        # to the same internal port.
        return make_port(int_pipe, pipe_local_port & 0x1F8)
    else:
        assert (arch == "tofino" or arch == "tofino2")


def get_port_from_pipes(pipes):
    ports = list()
    for pipe in pipes:
        ports = ports + swports_by_pipe[pipe]
    print('ports', ports)
    return random.choice(ports)


def verify_cntr_inc(test, target, dip, ttl, tag, num_pkts):
    logger.info("Verifying counter got incremented on external pipe egress")
    resp = test.a_forward_e.entry_get(target,
                                      [test.a_forward_e.make_key(
                                          [gc.KeyTuple('hdr.ipv4.dst_addr', dip, '255.255.255.255'),
                                           gc.KeyTuple('hdr.ipv4.ttl', ttl, 255),
                                           gc.KeyTuple('$MATCH_PRIORITY', 0)])],
                                      {"from_hw": True},
                                      test.a_forward_e.make_data(
                                          [gc.DataTuple("$COUNTER_SPEC_BYTES"),
                                           gc.DataTuple("$COUNTER_SPEC_PKTS")],
                                          'SwitchEgress_a.hit',
                                          get=True))

    # parse resp to get the counter
    data_dict = next(resp)[0].to_dict()
    recv_pkts = data_dict["$COUNTER_SPEC_PKTS"]
    recv_bytes = data_dict["$COUNTER_SPEC_BYTES"]

    if (num_pkts != recv_pkts):
        logger.error("Error! packets sent = %s received count = %s", str(num_pkts), str(recv_pkts))
        assert 0

    # Default packet size is 100 bytes and model adds 4 bytes of CRC
    # Add 2 bytes for the custom metadata header
    pkt_size = 100 + 4 + 2
    num_bytes = num_pkts * pkt_size

    if (num_bytes != recv_bytes):
        logger.error("Error! bytes sent = %s received count = %s", str(num_bytes), str(recv_bytes))
        assert 0


def get_all_tables(test):
    # Some of these tables can be retrieved using a lesser qualified name like storm_control
    # since it is not present in any other control block of the P4 program.  Other tables
    # such as forward or the port-metadata table need more specific names to uniquely identify
    # exactly which table is being requested.
    test.a_fwd_recirculation = test.bfrt_info.table_get("SwitchIngress_a.fwd_recirculation")
    test.a_fwd_e = test.bfrt_info.table_get("SwitchEgress_a.fwd")

    test.b_fwd_e = test.bfrt_info.table_get("SwitchEgress_b.fwd")
    test.b_fwd_recirculation = test.bfrt_info.table_get("SwitchIngress_b.fwd_recirculation")

    # Add annotations to a few fields to specify their type.
    test.a_fwd_e.info.key_field_annotation_add('hdr.ipv4.dst_addr', "ipv4")
    test.b_fwd_e.info.key_field_annotation_add('hdr.ipv4.dst_addr', "ipv4")

    # peregrine specific tables
    test.ip_src_pkt_mean = test.bfrt_info.table_get("SwitchIngress_a.stats_ip_src.pkt_mean")
    test.mac_src_ip_src_pkt_mean = test.bfrt_info.table_get("SwitchIngress_a.stats_mac_src_ip_src.pkt_mean")
    test.five_t_pkt_mean = test.bfrt_info.table_get("SwitchIngress_a.stats_five_t.pkt_mean")
    test.five_t_cov = test.bfrt_info.table_get("SwitchIngress_b.stats_five_t_2d.cov")
    test.five_t_std_dev_prod = test.bfrt_info.table_get("SwitchIngress_b.stats_five_t_2d.std_dev_prod")
    test.five_t_pcc = test.bfrt_info.table_get("SwitchIngress_b.stats_five_t_2d.pcc")
    test.ip_pkt_mean = test.bfrt_info.table_get("SwitchIngress_a.stats_ip.pkt_mean")
    test.ip_cov = test.bfrt_info.table_get("SwitchIngress_b.stats_ip_2d.cov")
    test.ip_std_dev_prod = test.bfrt_info.table_get("SwitchIngress_b.stats_ip_2d.std_dev_prod")
    test.ip_pcc = test.bfrt_info.table_get("SwitchIngress_b.stats_ip_2d.pcc")


def program_entries(test, target, ig_port, int_port, eg_port, tag, dmac, dip, ttl):

    print('ig_port', ig_port)
    print('int_port', int_port)
    print('eg_port', eg_port)
    print('tag', tag)
    print('dmac', dmac)
    print('dip', dip)
    print('ttl', ttl)

    logger.info("Programming table entries")

    logger.info(" Programming table entries on ingress ext-pipe")
    logger.info("    Table: fwd_recirculation")
    test.a_fwd_recirculation.entry_add(
        target,
        [test.a_fwd_recirculation.make_key(
            [gc.KeyTuple('ig_intr_md.ingress_port', ig_port)])],
        [test.a_fwd_recirculation.make_data(
            [gc.DataTuple('port', int_port)],
            'SwitchIngress_a.modify_eg_port')])

    logger.info(" Programming table entries on egress int-pipe")
    logger.info("    Table: fwd")
    test.b_fwd_e.entry_add(
        target,
        [test.b_fwd_e.make_key(
            [gc.KeyTuple('hdr.ipv4.dst_addr', dip, prefix_len=31),
             gc.KeyTuple('hdr.ipv4.ttl', ttl)])],
        [test.b_fwd_e.make_data([], "SwitchEgress_b.hit")])
    # The action will decrement the TTL and increment the tag so let's do the
    # same here so the variables are ready to use in the next table.
    ttl = ttl - 1
    tag = tag + 1

    logger.info(" Programming table entries on ingress int-pipe")
    logger.info("    Table: fwd_recirculation")
    test.b_fwd_recirculation.entry_add(
        target,
        [test.b_fwd_recirculation.make_key([gc.KeyTuple('ig_intr_md.ingress_port', int_port)])],
        [test.b_fwd_recirculation.make_data([gc.DataTuple('port', eg_port)],
                                            'SwitchIngress_b.modify_eg_port')])

    logger.info(" Programming table entries on egress ext-pipe")
    logger.info("    Table: fwd")
    test.a_fwd_e.entry_add(
        target,
        [test.a_fwd_e.make_key(
            [gc.KeyTuple('hdr.ipv4.dst_addr', dip, '255.255.255.255'),
             gc.KeyTuple('hdr.ipv4.ttl', ttl, 0xFF),
             gc.KeyTuple('$MATCH_PRIORITY', 0)])],
        [test.a_fwd_e.make_data([], 'SwitchEgress_a.hit')])

    # IP SRC MEAN TABLE RULES ###

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 2, 0b11111110)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_1')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 4, 0b11111100)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_2')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 8, 0b11111000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_3')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 16, 0b11110000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_4')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 32, 0b11100000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_5')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 64, 0b11000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_6')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 128, 0b10000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_7')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 256, 0b1111111100000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_8')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 512, 0b1111111000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_9')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 1024, 0b1111110000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_10')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 2048, 0b1111100000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_11')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 4096, 0b1111000000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_12')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 8192, 0b1110000000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_13')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 16384, 0b1100000000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_14')])

    test.ip_src_pkt_mean.entry_add(
        target,
        [test.ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                        gc.KeyTuple(str('ig_md.stats_ip_src.pkt_cnt_0'), 32768, 0b1000000000000000)])],
        [test.ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_15')])

    # MAC SRC IP SRC MEAN TABLE RULES

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 2,
                                                            0b11111110)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_1')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 4,
                                                            0b11111100)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_2')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 8,
                                                            0b11111000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_3')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 16,
                                                            0b11110000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_4')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 32,
                                                            0b11100000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_5')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 64,
                                                            0b11000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_6')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 128,
                                                            0b10000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_7')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 256,
                                                            0b1111111100000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_8')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 512,
                                                            0b1111111000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_9')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 1024,
                                                            0b1111110000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_10')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 2048,
                                                            0b1111100000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_11')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 4096,
                                                            0b1111000000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_12')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 8192,
                                                            0b1110000000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_13')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 16384,
                                                            0b1100000000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_14')])

    test.mac_src_ip_src_pkt_mean.entry_add(
        target,
        [test.mac_src_ip_src_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                                gc.KeyTuple(str('ig_md.stats_mac_src_ip_src.pkt_cnt_0'), 32768,
                                                            0b1000000000000000)])],
        [test.mac_src_ip_src_pkt_mean.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_15')])

    # FIVE T MEAN TABLE RULES

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 2, 0b11111110)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_1')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 4, 0b11111100)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_2')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 8, 0b11111000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_3')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 16, 0b11110000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_4')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 32, 0b11100000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_5')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 64, 0b11000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_6')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 128, 0b10000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_7')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 256, 0b1111111100000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_8')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 512, 0b1111111000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_9')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 1024, 0b1111110000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_10')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 2048, 0b1111100000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_11')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 4096, 0b1111000000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_12')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 8192, 0b1110000000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_13')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 16384, 0b1100000000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_14')])

    test.five_t_pkt_mean.entry_add(
        target,
        [test.five_t_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                        gc.KeyTuple(str('ig_md.stats_five_t.pkt_cnt_0'), 32768, 0b1000000000000000)])],
        [test.five_t_pkt_mean.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_15')])

    # FIVE T COV TABLE RULES

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 2, 0b11111110)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_1')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 4, 0b11111100)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_2')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 8, 0b11111000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_3')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 16, 0b11110000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_4')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 32, 0b11100000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_5')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 64, 0b11000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_6')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 128, 0b10000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_7')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 256, 0b1111111100000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_8')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 512, 0b1111111000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_9')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 1024, 0b1111110000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_10')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 2048, 0b1111100000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_11')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 4096, 0b1111000000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_12')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 8192, 0b1110000000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_13')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 16384, 0b1100000000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_14')])

    test.five_t_cov.entry_add(
        target,
        [test.five_t_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                   gc.KeyTuple(str('hdr.peregrine.five_t_pkt_cnt_1'), 32768, 0b1000000000000000)])],
        [test.five_t_cov.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_15')])

    # FIVE T STD DEV TABLE RULES

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 2, 0b11111110)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_1')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 4, 0b11111100)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_2')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 8, 0b11111000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_3')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 16, 0b11110000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_4')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 32, 0b11100000)])],
            [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_5')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 64, 0b11000000)])],
            [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_6')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 128, 0b10000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_7')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 256,
                                                        0b1111111100000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_8')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 512,
                                                        0b1111111000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_9')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 1024,
                                                        0b1111110000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_10')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 2048,
                                                        0b1111100000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_11')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 4096,
                                                        0b1111000000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_12')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 8192,
                                                        0b1110000000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_13')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 16384,
                                                        0b1100000000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_14')])

    test.five_t_std_dev_prod.entry_add(
        target,
        [test.five_t_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                            gc.KeyTuple(str('ig_md.stats_five_t.std_dev_0'), 32768,
                                                        0b1000000000000000)])],
        [test.five_t_std_dev_prod.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_15')])

    # FIVE T CORR COEF TABLE RULES

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 2, 0b11111110)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_1')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 4, 0b11111100)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_2')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 8, 0b11111000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_3')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 16, 0b11110000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_4')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 32, 0b11100000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_5')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 64, 0b11000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_6')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 128, 0b10000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_7')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 256, 0b1111111100000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_8')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 512, 0b1111111000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_9')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 1024, 0b1111110000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_10')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 2048, 0b1111100000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_11')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 4096, 0b1111000000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_12')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 8192, 0b1110000000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_13')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 16384, 0b1100000000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_14')])

    test.five_t_pcc.entry_add(
        target,
        [test.five_t_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                   gc.KeyTuple(str('ig_md.stats_five_t.std_dev_1'), 32768, 0b1000000000000000)])],
        [test.five_t_pcc.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_15')])

    # IP MEAN TABLE RULES ###

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 2, 0b11111110)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_1')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 4, 0b11111100)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_2')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 8, 0b11111000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_3')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 16, 0b11110000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_4')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 32, 0b11100000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_5')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 64, 0b11000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_6')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 128, 0b10000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_7')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 256, 0b1111111100000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_8')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 512, 0b1111111000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_9')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 1024, 0b1111110000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_10')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 2048, 0b1111100000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_11')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 4096, 0b1111000000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_12')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 8192, 0b1110000000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_13')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 16384, 0b1100000000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_14')])

    test.ip_pkt_mean.entry_add(
        target,
        [test.ip_pkt_mean.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                    gc.KeyTuple(str('ig_md.stats_ip.pkt_cnt_0'), 32768, 0b1000000000000000)])],
        [test.ip_pkt_mean.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_15')])

    # IP COV TABLE RULES

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 2, 0b11111110)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_1')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 4, 0b11111100)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_2')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 8, 0b11111000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_3')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 16, 0b11110000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_4')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 32, 0b11100000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_5')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 64, 0b11000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_6')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 128, 0b10000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_7')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 256, 0b1111111100000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_8')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 512, 0b1111111000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_9')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 1024, 0b1111110000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_10')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 2048, 0b1111100000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_11')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 4096, 0b1111000000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_12')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 8192, 0b1110000000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_13')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 16384, 0b1100000000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_14')])

    test.ip_cov.entry_add(
        target,
        [test.ip_cov.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                               gc.KeyTuple(str('hdr.peregrine.ip_pkt_cnt_1'), 32768, 0b1000000000000000)])],
        [test.ip_cov.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_15')])

    # IP STD DEV TABLE RULES

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 2, 0b11111110)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_1')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 4, 0b11111100)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_2')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 8, 0b11111000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_3')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 16, 0b11110000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_4')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 32, 0b11100000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_5')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 64, 0b11000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_6')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 128, 0b10000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_7')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 256, 0b1111111100000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_8')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 512, 0b1111111000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_9')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 1024, 0b1111110000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_10')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 2048, 0b1111100000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_11')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 4096, 0b1111000000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_12')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 8192, 0b1110000000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_13')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 16384, 0b1100000000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_14')])

    test.ip_std_dev_prod.entry_add(
        target,
        [test.ip_std_dev_prod.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                                        gc.KeyTuple(str('ig_md.stats_ip.std_dev_0'), 32768, 0b1000000000000000)])],
        [test.ip_std_dev_prod.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_15')])

    # IP CORR COEF TABLE RULES

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 15),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 2, 0b11111110)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_1')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 14),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 4, 0b11111100)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_2')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 13),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 8, 0b11111000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_3')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 12),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 16, 0b11110000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_4')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 11),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 32, 0b11100000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_5')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 10),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 64, 0b11000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_6')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 9),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 128, 0b10000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_7')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 8),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 256, 0b1111111100000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_8')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 7),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 512, 0b1111111000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_9')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 6),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 1024, 0b1111110000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_10')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 5),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 2048, 0b1111100000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_11')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 4),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 4096, 0b1111000000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_12')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 3),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 8192, 0b1110000000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_13')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 2),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 16384, 0b1100000000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_14')])

    test.ip_pcc.entry_add(
        target,
        [test.ip_pcc.make_key([gc.KeyTuple('$MATCH_PRIORITY', 1),
                               gc.KeyTuple(str('ig_md.stats_ip.std_dev_1'), 32768, 0b1000000000000000)])],
        [test.ip_pcc.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_15')])


def delete_entries(test, target):
    logger.info("Deleting table entries")

    logger.info(" Deleting table entries on external pipe ingress")
    logger.info("    Table: fwd_recirculation")
    test.a_fwd_recirculation.entry_del(target, [])

    logger.info(" Deleting table entries on internal pipe egress")
    logger.info("    Table: fwd")
    test.b_fwd_e.entry_del(target, [])

    logger.info(" Deleting table entries on internal pipe ingress")
    logger.info("    Table: fwd_recirculation")
    test.b_fwd_recirculation.entry_del(target, [])

    logger.info(" Deleting table entries on external pipe egress")
    logger.info("    Table: fwd")
    test.a_fwd_e.entry_del(target, [])

    test.ip_src_pkt_mean.entry_del(target, [])
    test.mac_src_ip_src_pkt_mean.entry_del(target, [])
    test.five_t_pkt_mean.entry_del(target, [])
    test.five_t_cov.entry_del(target, [])
    test.five_t_std_dev_prod.entry_del(target, [])
    test.five_t_pcc.entry_del(target, [])
    test.ip_pkt_mean.entry_del(target, [])
    test.ip_cov.entry_del(target, [])
    test.ip_std_dev_prod.entry_del(target, [])
    test.ip_pcc.entry_del(target, [])


# Symmetric table test. Program tables in both pipeline profiles symmetrically.
# Send packet on pipe 0 ingress and expect it to go to pipe 1 and then finally
# egress on pipe 0 egress.
# Pipe0 ingrss -> Pipe 1 Egress -> Pipe 1 Ingress -> Pipe 0 Egress
class Sym32Q(BfRuntimeTest):
    def setUp(self):
        client_id = 0
        p4_name = "peregrine"
        BfRuntimeTest.setUp(self, client_id, p4_name)
        self.bfrt_info = self.interface.bfrt_info_get(p4_name)
        get_all_tables(self)

    def runTest(self):
        logger.info("")

        print('external pipes ', external_pipes)
        ig_port = get_port_from_pipes(external_pipes)
        print('ig_port ', ig_port)
        eg_port = get_port_from_pipes(external_pipes)
        print('eg_port ', eg_port)

        int_port = get_internal_port_from_external(ig_port)
        print('int_port ', int_port)
        logger.info("Expected forwarding path:")
        logger.info(" 1. Ingress processing in external pipe %d, ingress port %d", port_to_pipe(ig_port), ig_port)
        logger.info(" 2. Egress processing in internal pipe %d, internal port %d", port_to_pipe(int_port), int_port)
        logger.info(" 3. Loopback on internal port %d", int_port)
        logger.info(" 4. Ingress processing in internal pipe %d, internal port %d", port_to_pipe(int_port), int_port)
        logger.info(" 5. Egress processing in external pipe %d, egress port %d", port_to_pipe(eg_port), eg_port)

        dmac = "00:11:22:33:44:66"
        dip = '5.6.7.8'
        ttl = 64
        tag = 100

        # Use the default "All Pipes" in the target.  This will result in table
        # operations (add/mod/del/etc.) to be applied to all pipes the table is
        # present in.  So, an add to a table in profile A will update the table
        # in all pipes profile A is applied to.
        target = gc.Target(device_id=0)

        try:
            # Add entries and send one packet, it should forward and come back.
            program_entries(self, target, ig_port, int_port, eg_port, tag, dmac, dip, ttl)

            logger.info("Sending packet on port %d", ig_port)
            pkt = testutils.simple_tcp_packet(eth_dst=dmac,
                                              ip_dst=dip,
                                              ip_ttl=ttl)
            testutils.send_packet(self, ig_port, pkt, count=1)

            pkt["IP"].ttl = pkt["IP"].ttl - 4
            exp_pkt = pkt
            logger.info("Expecting packet on port %d", eg_port)
            testutils.verify_packets(self, exp_pkt, [eg_port])

            verify_cntr_inc(self, target, dip, ttl-3, tag+2, 1)

            # Delete the entries and send another packet, it should be dropped.
            # delete_entries(self, target)
            # logger.info("")
            # logger.info("Sending another packet on port %d", ig_port)
            # pkt = testutils.simple_tcp_packet(eth_dst=dmac,
            #                                   ip_dst=dip,
            #                                   ip_ttl=ttl)
            # testutils.send_packet(self, ig_port, pkt)

            # logger.info("Packet is expected to get dropped.")
            # testutils.verify_no_other_packets(self)

        finally:
            # Call the entry cleanup function again incase of an error.
            delete_entries(self, target)
