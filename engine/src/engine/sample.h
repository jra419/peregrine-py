#pragma once

#include <stdint.h>

namespace peregrine {

typedef uint8_t mac_t[6];
typedef uint32_t ipv4_t;
typedef uint16_t port_t;

struct sample_t {
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
};

}  // namespace peregrine