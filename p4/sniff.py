from scapy.all import Packet, sniff, IntField, bind_layers, TCP, wrpcap, ls, hexdump, Raw


class Kitsune(Packet):
    name = 'kitsune'
    fields_desc = [IntField('ip_src_pkt_cnt', 0),
                   IntField('ip_src_mean', 0),
                   IntField('ip_src_variance', 0),
                   IntField('mac_src_ip_src_pkt_cnt', 0),
                   IntField('mac_src_ip_src_mean', 0),
                   IntField('mac_src_ip_src_variance', 0),
                   IntField('five_t_pkt_cnt', 0),
                   IntField('five_t_mean', 0),
                   IntField('five_t_variance', 0),
                   IntField('five_t_variance_neg', 0),
                   IntField('five_t_pkt_cnt_1', 0),
                   IntField('five_t_mean_1', 0),
                   IntField('five_t_mean_squared_0', 0),
                   IntField('five_t_variance_1', 0),
                   IntField('five_t_last_res', 0),
                   IntField('five_t_magnitude', 0),
                   IntField('five_t_radius', 0),
                   IntField('five_t_cov', 0),
                   IntField('five_t_pcc', 0),
                   IntField('ip_pkt_cnt', 0),
                   IntField('ip_mean', 0),
                   IntField('ip_variance', 0),
                   IntField('ip_variance_neg', 0),
                   IntField('ip_pkt_cnt_1', 0),
                   IntField('ip_mean_1', 0),
                   IntField('ip_mean_squared_0', 0),
                   IntField('ip_variance_1', 0),
                   IntField('ip_last_res', 0),
                   IntField('ip_magnitude', 0),
                   IntField('ip_radius', 0),
                   IntField('ip_cov', 0),
                   IntField('ip_pcc', 0)]


def callback(pkt):
    if Kitsune in pkt:
        pkt.show()
        # hexdump(pkt)
        # print(pkt.summary())
        # ls(pkt)
        # print(len(pkt[Raw]))
        # print(pkt[Kitsune].five_t_mean)
        wrpcap('test.pcap', pkt, append=True)


bind_layers(TCP, Kitsune, dport=64)
# sniff(iface='veth250', prn=callback)
sniff(filter='tcp and host 5.6.7.8', prn=callback)
