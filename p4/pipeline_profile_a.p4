#include <core.p4>
#include <tna.p4>
#include "includes/headers.p4"
#include "includes/constants.p4"
#include "includes/parser_a.p4"
#include "includes/deparser_a.p4"
#include "includes/stats/stats_mac_ip_src_a.p4"
#include "includes/stats/stats_ip_src_a.p4"
#include "includes/stats/stats_ip_a.p4"
#include "includes/stats/stats_five_t_a.p4"

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

    c_stats_ip_src_a()        stats_ip_src_a;
    c_stats_mac_ip_src_a()    stats_mac_ip_src_a;
    c_stats_ip_a()            stats_ip_a;
    c_stats_five_t_a()        stats_five_t_a;

    Register<decay_cntr, _>(1)  reg_decay_cntr;         // Current decay counter value.
    Register<bit<32>, _>(1)     reg_pkt_cnt_global;     // Global packet counter.
    Register<bit<32>, _>(1)     reg_pkt_len_squared;    // Squared packet length.

    RegisterAction<decay_cntr, _, bit<16>>(reg_decay_cntr) ract_decay_cntr_check = {
        void apply(inout decay_cntr decay, out bit<16> result) {
            if (decay.cur_pkt < SAMPLING) {
                if (decay.value < 24576) {
                    decay.value = decay.value + 8192;
                } else {
                    decay.value = 0;
                }
                decay.cur_pkt = decay.cur_pkt + 1;
            } else {
                decay.cur_pkt = 1;
            }
            result = decay.value;
        }
    };

    RegisterAction<_, _, bit<32>>(reg_pkt_cnt_global) ract_pkt_cnt_global = {
        void apply(inout bit<32> value, out bit<32> result) {
            value = value + 1;
            result = value;
        }
    };

    MathUnit<bit<32>>(MathOp_t.SQR, 1) square_pkt_len;
    RegisterAction<_, _, bit<32>>(reg_pkt_len_squared) ract_pkt_len_squared_calc = {
        void apply(inout bit<32> value, out bit<32> result) {
            value = square_pkt_len.execute((bit<32>)hdr.ipv4.len);
            result = value;
        }
    };

    action decay_cntr_check() {
        ig_md.meta.decay_cntr = ract_decay_cntr_check.execute(0);
    }

    // Timestamp bit-slicing from 48 bits to 32 bits.
    // Necessary to allow usage in reg. actions, which only support max 32 bits.
    action ts_conversion() {
        ig_md.meta.current_ts = ig_intr_md.ingress_mac_tstamp[47:16];
    }

    action pkt_cnt_global_calc() {
        ig_md.meta.pkt_cnt_global = ract_pkt_cnt_global.execute(0);
    }

    action pkt_len_squared_calc() {
        ig_md.meta.pkt_len_squared = ract_pkt_len_squared_calc.execute(0);
    }

    action modify_eg_port(PortId_t port) {
        ig_tm_md.ucast_egress_port = port;
        ig_tm_md.copy_to_cpu = 1;
        hdr.peregrine.forward = 1;
        hdr.peregrine.decay = (bit<32>)ig_md.meta.decay_cntr;
        hdr.peregrine.pkt_cnt_global = ig_md.meta.pkt_cnt_global;
    }

    action set_peregrine_mac_ip_src_a() {
        hdr.peregrine.setValid();
        hdr.peregrine.mac_ip_src_pkt_cnt = ig_md.stats_mac_ip_src.pkt_cnt_0;
        hdr.peregrine.mac_ip_src_pkt_len = ig_md.stats_mac_ip_src.pkt_len;
        hdr.peregrine.mac_ip_src_ss = ig_md.stats_mac_ip_src.ss;
        hdr.peregrine.ip_src_pkt_cnt = ig_md.stats_ip_src.pkt_cnt_0;
        hdr.peregrine.ip_src_pkt_len = ig_md.stats_ip_src.pkt_len;
        hdr.peregrine.ip_src_ss = ig_md.stats_ip_src.ss;
    }

    action set_peregrine_ip_a() {
        hdr.peregrine.ip_pkt_cnt = ig_md.stats_ip.pkt_cnt_0;
        hdr.peregrine.ip_pkt_cnt_1 = ig_md.stats_ip.pkt_cnt_1;
        hdr.peregrine.ip_ss_0 = ig_md.stats_ip.ss_0;
        hdr.peregrine.ip_ss_1 = ig_md.stats_ip.ss_1;
        hdr.peregrine.ip_mean_0 = ig_md.stats_ip.mean_0;
        hdr.peregrine.ip_mean_1 = ig_md.stats_ip.mean_1;
        hdr.peregrine.ip_sum_res_prod_cov = ig_md.stats_ip.sum_res_prod;
    }

    action set_peregrine_five_t_a() {
        hdr.peregrine.five_t_pkt_cnt = ig_md.stats_five_t.pkt_cnt_0;
        hdr.peregrine.five_t_pkt_cnt_1 = ig_md.stats_five_t.pkt_cnt_1;
        hdr.peregrine.five_t_ss_0 = ig_md.stats_five_t.ss_0;
        hdr.peregrine.five_t_ss_1 = ig_md.stats_five_t.ss_1;
        hdr.peregrine.five_t_mean_0 = ig_md.stats_five_t.mean_0;
        hdr.peregrine.five_t_mean_1 = ig_md.stats_five_t.mean_1;
        hdr.peregrine.five_t_sum_res_prod_cov = ig_md.stats_five_t.sum_res_prod;
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
    }

    apply {
        if (hdr.ipv4.isValid()) {

            // Global packet count calculation.
            pkt_cnt_global_calc();

            decay_cntr_check();

            // Timestamp bit-slicing.
            ts_conversion();

            // Squared packet len calculation.
            pkt_len_squared_calc();

            // Calculate stats.
            stats_ip_src_a.apply(hdr, ig_md);
            stats_mac_ip_src_a.apply(hdr, ig_md);
            stats_ip_a.apply(hdr, ig_md);
            stats_five_t_a.apply(hdr, ig_md);

            if (ig_md.meta.pkt_cnt_global % SAMPLING == 0) {
                fwd_recirculation.apply();
                set_peregrine_mac_ip_src_a();
                set_peregrine_ip_a();
                set_peregrine_five_t_a();
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
        hdr.peregrine.forward = 4;
    }

    action miss() {
        eg_intr_md_for_dprs.drop_ctl = 0x1; // Drop packet.
    }

    table fwd {
        key = {
            hdr.peregrine.forward : exact;
        }

        actions = {
            hit;
            @defaultonly miss;
        }

        const default_action = miss;
    }

    apply {
        fwd.apply();
    }
}

