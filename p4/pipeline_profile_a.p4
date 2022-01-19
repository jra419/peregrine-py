#include <core.p4>
#include <tna.p4>
#include "includes/headers.p4"
#include "includes/constants.p4"
#include "includes/parser_a.p4"
#include "includes/deparser_a.p4"
#include "includes/stats/stats_ip_src.p4"
#include "includes/stats/stats_ip.p4"
#include "includes/stats/stats_mac_src_ip_src.p4"
#include "includes/stats/stats_five_t.p4"

#define FORWARD_TABLE_SIZE 1024

// ---------------------------------------------------------------------------
// Pipeline A
// ---------------------------------------------------------------------------

control SwitchIngress_a(
        inout header_t hdr,
        inout ingress_metadata_a_t ig_md,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
        inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
        inout ingress_intrinsic_metadata_for_tm_t ig_tm_md) {

    // Control block instantiations.

    c_stats_ip_src()            stats_ip_src;
    c_stats_mac_src_ip_src()    stats_mac_src_ip_src;
    c_stats_five_t()            stats_five_t;
    c_stats_ip()                stats_ip;

    // Squared packet length.
    Register<bit<32>, _>(1) reg_pkt_len_squared;

    MathUnit<bit<32>>(MathOp_t.SQR, 1) square_pkt_len;
    RegisterAction<_, _, bit<32>>(reg_pkt_len_squared) ract_pkt_len_squared_calc = {
        void apply(inout bit<32> value, out bit<32> result) {
            value = square_pkt_len.execute((bit<32>)hdr.ipv4.len);
            result = value;
        }
    };

    // Timestamp bit-slicing from 48 bits to 32 bits.
    // Necessary to allow usage in reg. actions, which only support max 32 bits.
    action ts_conversion() {
        ig_md.meta.current_ts = ig_intr_md.ingress_mac_tstamp[47:16];
    }

    action pkt_len_squared_calc() {
        ig_md.meta.pkt_len_squared = ract_pkt_len_squared_calc.execute(0);
    }

    action modify_eg_port(PortId_t port) {
        ig_tm_md.ucast_egress_port = port;
    }

    table fwd_recirculation {
        key = {
            ig_intr_md.ingress_port : exact;
        }

        actions = {
            NoAction;
            modify_eg_port;
        }

        const default_action = NoAction;
        size = 512;
    }

    action set_peregrine_mac_ip_src() {
        hdr.peregrine.setValid();
        hdr.peregrine.ip_src_pkt_cnt = ig_md.stats_ip_src.pkt_cnt_0;
        hdr.peregrine.ip_src_mean = ig_md.stats_ip_src.mean_0;
        hdr.peregrine.ip_src_variance = ig_md.stats_ip_src.variance_0;
        hdr.peregrine.mac_src_ip_src_pkt_cnt = ig_md.stats_mac_src_ip_src.pkt_cnt_0;
        hdr.peregrine.mac_src_ip_src_mean = ig_md.stats_mac_src_ip_src.mean_0;
        hdr.peregrine.mac_src_ip_src_variance = ig_md.stats_mac_src_ip_src.variance_0;
    }

    action set_peregrine_five_t() {
        hdr.peregrine.five_t_hash_0 = ig_md.hash.five_t_0;
        hdr.peregrine.five_t_hash_1 = ig_md.hash.five_t_1;
        hdr.peregrine.five_t_pkt_cnt = ig_md.stats_five_t.pkt_cnt_0;
        hdr.peregrine.five_t_mean = ig_md.stats_five_t.mean_0;
        hdr.peregrine.five_t_variance = ig_md.stats_five_t.variance_0;
        hdr.peregrine.five_t_variance_neg = ig_md.stats_five_t.variance_0_neg;
        hdr.peregrine.five_t_pkt_cnt_1 = ig_md.stats_five_t.pkt_cnt_1;
        hdr.peregrine.five_t_mean_1 = ig_md.stats_five_t.mean_1;
        hdr.peregrine.five_t_mean_squared_0 = ig_md.stats_five_t.mean_squared_0;
        hdr.peregrine.five_t_variance_1 = ig_md.stats_five_t.variance_1;
        hdr.peregrine.five_t_last_res = ig_md.stats_five_t.last_res;
    }

    action set_peregrine_ip() {
        hdr.peregrine.ip_hash_0 = ig_md.hash.ip_0;
        hdr.peregrine.ip_hash_1 = ig_md.hash.ip_1;
        hdr.peregrine.ip_pkt_cnt = ig_md.stats_ip.pkt_cnt_0;
        hdr.peregrine.ip_mean = ig_md.stats_ip.mean_0;
        hdr.peregrine.ip_variance = ig_md.stats_ip.variance_0;
        hdr.peregrine.ip_variance_neg = ig_md.stats_ip.variance_0_neg;
        hdr.peregrine.ip_pkt_cnt_1 = ig_md.stats_ip.pkt_cnt_1;
        hdr.peregrine.ip_mean_1 = ig_md.stats_ip.mean_1;
        hdr.peregrine.ip_mean_squared_0 = ig_md.stats_ip.mean_squared_0;
        hdr.peregrine.ip_variance_1 = ig_md.stats_ip.variance_1;
        hdr.peregrine.ip_last_res = ig_md.stats_ip.last_res;
    }

    apply {
        if (hdr.ipv4.isValid()) {

            // Timestamp bit-slicing.
            ts_conversion();

            // Squared packet len calculation.
            pkt_len_squared_calc();

            // Calculate stats.
            stats_ip_src.apply(hdr, ig_md);
            stats_mac_src_ip_src.apply(hdr, ig_md);
            stats_five_t.apply(hdr, ig_md);
            stats_ip.apply(hdr, ig_md);

            if (ig_md.stats_five_t.pkt_cnt_0 % 1 == 0 ||
                ig_md.stats_mac_src_ip_src.pkt_cnt_0 % 1 == 0 ||
                ig_md.stats_ip.pkt_cnt_0 % 1 == 0 ||
                ig_md.stats_ip_src.pkt_cnt_0 % 1 == 0) {
                    fwd_recirculation.apply();
                    set_peregrine_mac_ip_src();
                    set_peregrine_five_t();
                    set_peregrine_ip();
            }
        }
    }
}

control SwitchEgress_a(
    inout header_t hdr,
    inout egress_metadata_a_t eg_md,
    in egress_intrinsic_metadata_t eg_intr_md,
    in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
    inout egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprs,
    inout egress_intrinsic_metadata_for_output_port_t eg_intr_md_for_oport) {

    action hit() {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.tcp.dst_port = 64;
        hdr.ipv4.len = hdr.ipv4.len + 100;
    }

    action miss() {
        eg_intr_md_for_dprs.drop_ctl = 0x1; // Drop packet.
    }

    table fwd {
        key = {
            hdr.ipv4.dst_addr : ternary;
            hdr.ipv4.ttl : ternary;
        }

        actions = {
            hit;
            @defaultonly miss;
        }

        const default_action = miss;
        size = FORWARD_TABLE_SIZE;
    }

    apply {
        fwd.apply();
    }
}

