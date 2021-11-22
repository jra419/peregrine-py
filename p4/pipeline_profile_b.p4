/*******************************************************************************
 * BAREFOOT NETWORKS CONFIDENTIAL & PROPRIETARY
 *
 * Copyright (c) 2019-present Barefoot Networks, Inc.
 *
 * All Rights Reserved.
 *
 * NOTICE: All information contained herein is, and remains the property of
 * Barefoot Networks, Inc. and its suppliers, if any. The intellectual and
 * technical concepts contained herein are proprietary to Barefoot Networks, Inc.
 * and its suppliers and may be covered by U.S. and Foreign Patents, patents in
 * process, and are protected by trade secret or copyright law.  Dissemination of
 * this information or reproduction of this material is strictly forbidden unless
 * prior written permission is obtained from Barefoot Networks, Inc.
 *
 * No warranty, explicit or implicit is provided, unless granted under a written
 * agreement with Barefoot Networks, Inc.
 *
 ******************************************************************************/

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
// P4 Pipeline b
// Packet travels through different table types (exm, alpm), each of which
// decrement the ipv4 ttl on a table hit.
// Mac Learning is also done thorugh one table.
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

    /*
    action hit() {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action miss() {
        ig_dprsr_md.drop_ctl = 0x1; // Drop packet.
    }

    table fwd {
        key = {
            hdr.ipv4.dst_addr : exact;
            hdr.ipv4.ttl : exact;
        }

        actions = {
            hit;
            miss;
        }

        const default_action = miss;
        size = FORWARD_TABLE_SIZE;
    }
    */

    /*
    action dmac_hit() {
    }

    action dmac_miss() {
        ig_dprsr_md.digest_type = 0;
    }

    table learning {
        key = {
            hdr.ethernet.dst_addr : exact;
        }

        actions = {
            dmac_hit;
            dmac_miss;
        }

        const default_action = dmac_miss;
        size = 2048;
    }
    */

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


    action set_kitsune_ip_2d() {
        hdr.kitsune.ip_magnitude = ig_md.stats_ip.magnitude;
        hdr.kitsune.ip_radius = ig_md.stats_ip.radius;
        hdr.kitsune.ip_cov = ig_md.stats_ip.cov;
        hdr.kitsune.ip_pcc = ig_md.stats_ip.pcc;
    }

    action set_kitsune_five_t_2d() {
        hdr.kitsune.five_t_magnitude = ig_md.stats_five_t.magnitude;
        hdr.kitsune.five_t_radius = ig_md.stats_five_t.radius;
        hdr.kitsune.five_t_cov = ig_md.stats_five_t.cov;
        hdr.kitsune.five_t_pcc = ig_md.stats_five_t.pcc;
    }

    apply {

        // Calculate stats.
        stats_five_t_2d.apply(hdr, ig_md, ig_intr_md);
        stats_ip_2d.apply(hdr, ig_md, ig_intr_md);

        /* fwd.apply(); */
        /* learning.apply(); */
        fwd_recirculation.apply();
        set_kitsune_five_t_2d();
        set_kitsune_ip_2d();
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

    @alpm(1)
    @alpm_partitions(1024)
    @alpm_subtrees_per_partition(2)
    table fwd {
        key = {
            hdr.ipv4.dst_addr : lpm;
            hdr.ipv4.ttl : exact;
        }

        actions = {
            hit;
            miss;
        }

        const default_action = miss;
        size = FORWARD_TABLE_SIZE;
    }

    apply {
        fwd.apply();
    }

}
