#include <core.p4>
#include <tna.p4>
#include "includes/headers.p4"
#include "includes/constants.p4"
#include "includes/parser_b.p4"
#include "includes/deparser_b.p4"
#include "includes/stats/stats_five_t_2d.p4"
#include "includes/stats/stats_ip_2d.p4"

#define FORWARD_TABLE_SIZE 1024

// ---------------------------------------------------------------------------
// Pipeline B
// ---------------------------------------------------------------------------

control SwitchIngress_b(
        inout header_t hdr,
        inout ingress_metadata_b_t ig_md,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
        inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
        inout ingress_intrinsic_metadata_for_tm_t ig_tm_md) {

    // Control block instantiations.

    c_stats_five_t_2d()     stats_five_t_2d;
    c_stats_ip_2d()         stats_ip_2d;

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

    action set_peregrine_ip_2d() {
        hdr.peregrine.ip_magnitude = ig_md.stats_ip.magnitude;
        hdr.peregrine.ip_radius = ig_md.stats_ip.radius;
        hdr.peregrine.ip_cov = ig_md.stats_ip.cov;
        hdr.peregrine.ip_pcc = ig_md.stats_ip.pcc;
    }

    action set_peregrine_five_t_2d() {
        hdr.peregrine.five_t_magnitude = ig_md.stats_five_t.magnitude;
        hdr.peregrine.five_t_radius = ig_md.stats_five_t.radius;
        hdr.peregrine.five_t_cov = ig_md.stats_five_t.cov;
        hdr.peregrine.five_t_pcc = ig_md.stats_five_t.pcc;
    }

    apply {

        // Calculate stats.
        stats_five_t_2d.apply(hdr, ig_md, ig_intr_md);
        stats_ip_2d.apply(hdr, ig_md, ig_intr_md);

        fwd_recirculation.apply();
        set_peregrine_five_t_2d();
        set_peregrine_ip_2d();
    }
}

control SwitchEgress_b(
    inout header_t hdr,
    inout egress_metadata_b_t eg_md,
    in egress_intrinsic_metadata_t eg_intr_md,
    in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
    inout egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprs,
    inout egress_intrinsic_metadata_for_output_port_t eg_intr_md_for_oport) {


    action hit() {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action miss() {
        eg_intr_md_for_dprs.drop_ctl = 0x1; // Drop packet.
    }

    table fwd {
        key = {
            /* hdr.ipv4.dst_addr : ternary; */
            hdr.ipv4.ttl : ternary;
            /* hdr.tcp.res : exact; */
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
