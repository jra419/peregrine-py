#ifndef _HEADERS_
#define _HEADERS_

header ethernet_t {
    bit<48> dst_addr;
    bit<48> src_addr;
    bit<16> ether_type;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> len;
    bit<16> identification;
    bit<3>  flags;
    bit<13> frag_offset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdr_checksum;
    bit<32> src_addr;
    bit<32> dst_addr;
}

header tcp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<32> seq_no;
    bit<32> ack_no;
    bit<4>  data_offset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgent_ptr;
}

header udp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> length_;
    bit<16> checksum;
}

header icmp_t {
    bit<8> type;
    bit<8> code;
    bit<16> hdrChecksum;
}

header peregrine_t {
    bit<32> ip_src_pkt_cnt;
    bit<32> ip_src_mean;
    bit<32> ip_src_variance;
    bit<32> mac_src_ip_src_pkt_cnt;
    bit<32> mac_src_ip_src_mean;
    bit<32> mac_src_ip_src_variance;
    bit<16> five_t_hash_0;
    bit<32> five_t_pkt_cnt;
    bit<32> five_t_mean;
    bit<32> five_t_variance;
    bit<32> five_t_variance_neg;
    bit<32> five_t_pkt_cnt_1;
    bit<32> five_t_mean_1;
    bit<32> five_t_mean_squared_0;
    bit<32> five_t_variance_1;
    bit<32> five_t_last_res;
    bit<32> five_t_std_dev_0;
    bit<32> five_t_magnitude;
    bit<32> five_t_radius;
    bit<32> five_t_cov;
    bit<32> five_t_pcc;
    bit<32> ip_pkt_cnt;
    bit<16> ip_hash_0;
    bit<32> ip_mean;
    bit<32> ip_variance;
    bit<32> ip_variance_neg;
    bit<32> ip_pkt_cnt_1;
    bit<32> ip_mean_1;
    bit<32> ip_mean_squared_0;
    bit<32> ip_variance_1;
    bit<32> ip_last_res;
    bit<32> ip_std_dev_0;
    bit<32> ip_magnitude;
    bit<32> ip_radius;
    bit<32> ip_cov;
    bit<32> ip_pcc;
}

header meta_t {
    bit<16> l4_src_port;
    bit<16> l4_dst_port;
    bit<16> decay_cntr;
    bit<32> decay_const;
    bit<32> decay_reg_add;
    bit<32> current_ts;
    bit<32> pkt_len_squared;
}

header decay_t {
    bit <32> decay_const;
}

header hash_meta_t {
    bit<16> mac_src_ip_src;
    bit<16> ip_src;
    bit<16> ip_0;
    bit<16> ip_1;
    bit<16> five_t_0;
    bit<16> five_t_1;
}

header stats_meta_t {
    bit<7> padding;
    bit<1> decay_check;
    bit<32> pkt_cnt_0;
    bit<32> pkt_cnt_1;
    bit<32> pkt_len;
    bit<32> mean_0;
    bit<32> mean_1;
    bit<32> mean_squared_0;
    bit<32> mean_squared_1;
    bit<32> mean_ss;
    bit<32> ss;
    bit<32> residue;
    bit<32> last_res;
    bit<32> res_prod;
    bit<32> sum_res_prod;
    bit<32> variance_0;
    bit<32> variance_0_neg;
    bit<32> variance_1;
    bit<32> variance_squared_0;
    bit<32> variance_squared_1;
    bit<32> std_dev_0;
    bit<32> std_dev_1;
    bit<32> std_dev_prod;
    bit<32> magnitude;
    bit<32> radius;
    bit<32> cov;
    bit<32> pcc;
}

struct ingress_metadata_a_t {
    bool            checksum_err;
    meta_t 	        meta;
    decay_t         decay;
    hash_meta_t     hash;
    stats_meta_t    stats_mac_src_ip_src;
    stats_meta_t    stats_ip_src;
    stats_meta_t    stats_ip;
    stats_meta_t    stats_five_t;
}

struct ingress_metadata_b_t {
    bool            checksum_err;
    meta_t 	        meta;
    hash_meta_t     hash;
    stats_meta_t    stats_ip;
    stats_meta_t    stats_five_t;
}

struct egress_metadata_a_t {}

struct egress_metadata_b_t {}

header bridged_metadata_t {
    // user-defined metadata carried over from ingress to egress.
    bit<16> rewrite;
    bit<1> psp;         // Penultimate Segment Pop
    bit<1> usp;         // Ultimate Segment Pop
    bit<1> decap;
    bit<1> encap;
    bit<4> pad;
}

struct header_t {
    bridged_metadata_t  bridged_md;
    ethernet_t	        ethernet;
    ipv4_t		        ipv4;
    tcp_t		        tcp;
    udp_t		        udp;
    icmp_t 		        icmp;
    peregrine_t         peregrine;
}

#endif
