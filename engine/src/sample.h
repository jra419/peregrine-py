#pragma once

#include <stdint.h>

#include "packet.h"

namespace peregrine {

struct sample_t {
	bool valid;

	mac_t mac_src;
	ipv4_t ip_src;
	ipv4_t ip_dst;
	uint8_t ip_proto;
	port_t port_src;
	port_t port_dst;
	uint32_t decay;
	uint32_t mac_ip_src_pkt_cnt;
	uint32_t mac_ip_src_mean;
	uint32_t mac_ip_src_std_dev;
	uint32_t ip_src_pkt_cnt;
	uint32_t ip_src_mean;
	uint32_t ip_src_std_dev;
	uint32_t ip_pkt_cnt;
	uint32_t ip_mean_0;
	uint32_t ip_std_dev_0;
	uint32_t ip_magnitude;
	uint32_t ip_radius;
	uint32_t five_t_pkt_cnt;
	uint32_t five_t_mean_0;
	uint32_t five_t_std_dev_0;
	uint32_t five_t_magnitude;
	uint32_t five_t_radius;
	uint64_t ip_sum_res_prod_cov;
	uint64_t ip_pcc;
	uint64_t five_t_sum_res_prod_cov;
	uint64_t five_t_pcc;

	sample_t(pkt_hdr_t* pkt, ssize_t pkt_size) {
		valid = pkt->has_valid_protocol();

		if (!valid) {
#ifdef DEBUG
			printf("Invalid protocol packet. Ignoring.\n");
#endif
			return;
		}

		valid =
			(pkt_size >= (pkt->get_l2_size() + pkt->get_l3_size() +
						  pkt->get_l4_size() + pkt->get_peregrine_hdr_size()));

		if (!valid) {
#ifdef DEBUG
			printf("Packet too small. Ignoring.\n");
#endif
			return;
		}

		auto l2 = pkt->get_l2();
		auto l3 = pkt->get_l3();
		auto l4 = pkt->get_l4();

		for (auto byte = 0; byte < sizeof(mac_t); byte++) {
			mac_src[byte] = l2->src_mac[byte];
		}


		ip_src   = l3->src_ip;
		ip_dst   = l3->dst_ip;
		ip_proto = l3->protocol;

		switch (ip_proto) {
			case IP_PROTO_TCP: {
				auto tcp_hdr = (tcp_hdr_t*)l4.first;
				port_src = tcp_hdr->src_port;
				port_dst = tcp_hdr->dst_port;
			} break;
			case IP_PROTO_UDP: {
				auto udp_hdr = (udp_hdr_t*)l4.first;
				port_src = udp_hdr->src_port;
				port_dst = udp_hdr->dst_port;
			} break;
			case IP_PROTO_ICMP: {
				auto icmp_hdr = (icmp_hdr_t*)l4.first;
				port_src = 0;
				port_dst = 0;
			} break;
		}

		auto peregrine_hdr = pkt->get_peregrine_hdr();

		decay = peregrine_hdr->decay;
		mac_ip_src_pkt_cnt = peregrine_hdr->mac_ip_src_pkt_cnt;
		mac_ip_src_mean = peregrine_hdr->mac_ip_src_mean;
		mac_ip_src_std_dev = peregrine_hdr->mac_ip_src_std_dev;
		ip_src_pkt_cnt = peregrine_hdr->ip_src_pkt_cnt;
		ip_src_mean = peregrine_hdr->ip_src_mean;
		ip_src_std_dev = peregrine_hdr->ip_src_std_dev;
		ip_pkt_cnt = peregrine_hdr->ip_pkt_cnt;
		ip_mean_0 = peregrine_hdr->ip_mean_0;
		ip_std_dev_0 = peregrine_hdr->ip_std_dev_0;
		ip_magnitude = peregrine_hdr->ip_magnitude;
		ip_radius = peregrine_hdr->ip_radius;
		five_t_pkt_cnt = peregrine_hdr->five_t_pkt_cnt;
		five_t_mean_0 = peregrine_hdr->five_t_mean_0;
		five_t_std_dev_0 = peregrine_hdr->five_t_std_dev_0;
		five_t_magnitude = peregrine_hdr->five_t_magnitude;
		five_t_radius = peregrine_hdr->five_t_radius;
		ip_sum_res_prod_cov = peregrine_hdr->ip_sum_res_prod_cov;
		ip_pcc = peregrine_hdr->ip_pcc;
		five_t_sum_res_prod_cov = peregrine_hdr->five_t_sum_res_prod_cov;
		five_t_pcc = peregrine_hdr->five_t_pcc;
	}
};

}  // namespace peregrine