import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc
from Table import Table


class FwdRecirculation_a(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FwdRecirculation_a, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('a_fwd_recirculation')
        self.logger.info('Setting up a_fwd_recirculation table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_a.fwd_recirculation')

        # clear and add defaults
        self.clear()

    def add_entry(self, ig_port, int_port):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on a_fwd_recirculation table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('ig_intr_md.ingress_port', ig_port)])],
           [self.table.make_data(
               [gc.DataTuple('port', int_port)],
               'SwitchIngress_a.modigy_eg_port')])


class FwdRecirculation_b(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FwdRecirculation_b, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('b_fwd_recirculation')
        self.logger.info('Setting up b_fwd_recirculation table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.fwd_recirculation')

        # clear and add defaults
        self.clear()

    def add_entry(self, ig_port, eg_port):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on b_fwd_recirculation table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('ig_intr_md.ingress_port', ig_port)])],
           [self.table.make_data(
               [gc.DataTuple('port', eg_port)],
               'SwitchIngress_b.modigy_eg_port')])


class Fwd_a(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(Fwd_a, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('a_fwd')
        self.logger.info('Setting up a_fwd table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchEgress_a.fwd')

        # Add anotations
        self.table.info.key_field_annotation_add('hdr.ipv4.dst_addr', 'ipv4')

        # clear and add defaults
        self.clear()

    def add_entry(self, dip, ttl):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on a_fwd table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('hdr.ipv4.dst_addr', dip, '255.255.255.255'),
                gc.KeyTuple('hdr.ipv4.ttl', ttl, 0xFF),
                gc.KeyTuple('$MATCH_PRIORITY', 0)])],
           [self.table.make_data([], 'SwitchEgress_a.hit')])


class Fwd_b(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(Fwd_b, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('b_fwd')
        self.logger.info('Setting up b_fwd table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchEgress_b.fwd')

        # Add anotations
        self.table.info.key_field_annotation_add('hdr.ipv4.dst_addr', 'ipv4')

        # clear and add defaults
        self.clear()

    def add_entry(self, dip, ttl):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on b_fwd table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('hdr.ipv4.dst_addr', dip, prefix_len=31),
                gc.KeyTuple('hdr.ipv4.ttl', ttl)])],
           [self.table.make_data([], 'SwitchEgress_b.hit')])


class MacSrcIpSrcPktMean(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(MacSrcIpSrcPktMean, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('mac_src_ip_src_pkt_mean')
        self.logger.info('Setting up mac_src_ip_src_pkt_mean table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_a.stats_mac_src_ip_src.pkt_mean')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on mac_src_ip_src_pkt_mean table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_mac_src_ip_src.pkt_cnt_0', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_a.stats_mac_src_ip_src.rshift_mean_' + str(div))])


class IpSrcPktMean(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(IpSrcPktMean, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('ip_src_pkt_mean')
        self.logger.info('Setting up ip_src_pkt_mean table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_a.stats_ip_src.pkt_mean')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on ip_src_pkt_mean table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_ip_src.pkt_cnt_0', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_a.stats_ip_src.rshift_mean_' + str(div))])


class IpPktMean(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(IpPktMean, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('ip_pkt_mean')
        self.logger.info('Setting up ip_pkt_mean table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_a.stats_ip.pkt_mean')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on ip_pkt_mean table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_ip.pkt_cnt_0', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_a.stats_ip.rshift_mean_' + str(div))])


class IpCov(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(IpPktMean, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('ip_cov')
        self.logger.info('Setting up ip_cov table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_ip_2d.cov')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on ip_cov table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('hdr.peregrine.ip_pkt_cnt_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_cov_' + str(div))])


class IpStdDevProd(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(IpStdDevProd, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('ip_std_dev_prod')
        self.logger.info('Setting up ip_std_dev_prod table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_ip_2d.std_dev_prod')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on ip_std_dev_prod table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_ip.std_dev_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_ip_2d.lshift_std_dev_prod_' + str(div))])


class IpPcc(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(IpPcc, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('ip_pcc')
        self.logger.info('Setting up ip_pcc table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_ip_2d.pcc')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on ip_pcc table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_ip.std_dev_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_ip_2d.rshift_pcc_' + str(div))])


class FiveTPktMean(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FiveTPktMean, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('five_t_pkt_mean')
        self.logger.info('Setting up five_t_pkt_mean table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_a.stats_five_t.pkt_mean')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on five_t_pkt_mean table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_five_t.pkt_cnt_0', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_a.stats_five_t.rshift_mean_' + str(div))])


class FiveTCov(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FiveTCov, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('five_t_cov')
        self.logger.info('Setting up five_t_cov table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_five_t_2d.cov')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on five_t_cov table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('hdr.peregrine.five_t_pkt_cnt_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_cov_' + str(div))])


class FiveTStdDevProd(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FiveTStdDevProd, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('five_t_std_dev_prod')
        self.logger.info('Setting up five_t_std_dev_prod table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_five_t_2d.std_dev_prod')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on five_t_std_dev_prod table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_five_t.std_dev_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_five_t_2d.lshift_std_dev_prod_' + str(div))])


class FiveTPcc(Table):

    def __init__(self, client, bfrt_info):
        # set up base class
        super(FiveTPcc, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('five_t_pcc')
        self.logger.info('Setting up five_t_pcc table...')

        # get this table
        self.table = self.bfrt_info.table_get('SwitchIngress_b.stats_five_t_2d.pcc')

        # clear and add defaults
        self.clear()

    def add_entry(self, priority, power, mask, div):
        # target all pipes on device 0
        target = gc.Target(device_id=0)

        self.logger.info('Programming entries on five_t_pcc table...')

        self.table.entry_add(
           target,
           [self.table.make_key(
               [gc.KeyTuple('MATCH_PRIORITY', priority),
                gc.KeyTuple('ig_md.stats_five_t.std_dev_1', power, mask)])],
           [self.table.make_data([], 'SwitchIngress_b.stats_five_t_2d.rshift_pcc_' + str(div))])
