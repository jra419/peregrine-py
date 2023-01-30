#pragma once

#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>

#include <string>

#define IP_PROTO_ICMP 1
#define IP_PROTO_TCP 6
#define IP_PROTO_UDP 17

#define MAX_PACKET_SIZE 10000

namespace peregrine {

typedef uint8_t mac_t[6];
typedef uint32_t ipv4_t;
typedef uint16_t port_t;

struct eth_hdr_t {
	mac_t dst_mac;
	mac_t src_mac;
	uint16_t eth_type;
} __attribute__((packed));

struct ipv4_hdr_t {
	uint8_t ihl : 4;
	uint8_t version : 4;
	uint8_t ecn : 2;
	uint8_t dscp : 6;
	uint16_t tot_len;
	uint16_t id;
	uint16_t frag_off;
	uint8_t ttl;
	uint8_t protocol;
	uint16_t check;
	ipv4_t src_ip;
	ipv4_t dst_ip;
} __attribute__((packed));

struct tcp_hdr_t {
	uint16_t src_port;
	uint16_t dst_port;
	uint32_t seq_no;
	uint32_t ack_no;
	uint16_t opts;
	uint16_t window;
	uint16_t checksum;
	uint16_t urgent_ptr;
} __attribute__((packed));

struct udp_hdr_t {
	port_t src_port;
	port_t dst_port;
	uint16_t length;
	uint16_t checksum;
} __attribute__((packed));

struct icmp_hdr_t {
	uint8_t type;
	uint8_t code;
	uint16_t checksum;
} __attribute__((packed));

struct peregrine_hdr_t {
	uint32_t decay;
	uint32_t mac_ip_src_pkt_cnt;
	uint32_t mac_ip_src_pkt_len;
	uint32_t mac_ip_src_ss;
	uint32_t mac_ip_src_mean;
	uint32_t mac_ip_src_std_dev;
	uint32_t ip_src_pkt_cnt;
	uint32_t ip_src_pkt_len;
	uint32_t ip_src_ss;
	uint32_t ip_src_mean;
	uint32_t ip_src_std_dev;
	uint32_t ip_pkt_cnt;
	uint32_t ip_ss_0;
	uint32_t ip_ss_1;
	uint32_t ip_mean_0;
	uint32_t ip_pkt_cnt_1;
	uint32_t ip_mean_1;
	uint32_t ip_std_dev_0;
	uint32_t ip_magnitude;
	uint32_t ip_radius;
	uint32_t five_t_pkt_cnt;
	uint32_t five_t_ss_0;
	uint32_t five_t_ss_1;
	uint32_t five_t_mean_0;
	uint32_t five_t_pkt_cnt_1;
	uint32_t five_t_mean_1;
	uint32_t five_t_std_dev_0;
	uint32_t five_t_magnitude;
	uint32_t five_t_radius;
	uint64_t ip_sum_res_prod_cov;
	uint64_t ip_pcc;
	uint64_t five_t_sum_res_prod_cov;
	uint64_t five_t_pcc;
} __attribute__((packed));

std::string mac_to_str(mac_t mac);
std::string ip_to_str(ipv4_t ip);
std::string port_to_str(port_t port);

struct pkt_hdr_t {
	uint8_t buffer[MAX_PACKET_SIZE];

	eth_hdr_t* get_l2() const { return (eth_hdr_t*)((uint8_t*)buffer); }

	size_t get_l2_size() const { return sizeof(eth_hdr_t); }

	ipv4_hdr_t* get_l3() const {
		auto l2_hdr = get_l2();
		auto l2_hdr_size = get_l2_size();
		return (ipv4_hdr_t*)((uint8_t*)l2_hdr + l2_hdr_size);
	}

	size_t get_l3_size() const { return sizeof(ipv4_hdr_t); }

	std::pair<void*, uint16_t> get_l4() const {
		auto ip_hdr = get_l3();
		auto ip_size = get_l3_size();

		switch (ip_hdr->protocol) {
			case IP_PROTO_TCP: {
				return std::pair<void*, uint16_t>((uint8_t*)ip_hdr + ip_size,
												  IP_PROTO_TCP);
			} break;
			case IP_PROTO_UDP: {
				return std::pair<void*, uint16_t>((uint8_t*)ip_hdr + ip_size,
												  IP_PROTO_UDP);
			} break;
			case IP_PROTO_ICMP: {
				return std::pair<void*, uint16_t>((uint8_t*)ip_hdr + ip_size,
												  IP_PROTO_ICMP);
			} break;
			default: {
				printf("\n*** Not TCP/UDP/ICMP packet! ***\n");
				exit(1);
			} break;
		}
	}

	bool has_valid_protocol() const {
		auto ip_hdr = get_l3();
		return (ip_hdr->protocol == IP_PROTO_TCP ||
				ip_hdr->protocol == IP_PROTO_UDP ||
				ip_hdr->protocol == IP_PROTO_ICMP);
	}

	size_t get_l4_size() const {
		auto ip_hdr = get_l3();

		switch (ip_hdr->protocol) {
			case IP_PROTO_TCP: {
				return sizeof(tcp_hdr_t);
			} break;
			case IP_PROTO_UDP: {
				return sizeof(udp_hdr_t);
			} break;
			case IP_PROTO_ICMP: {
				return sizeof(icmp_hdr_t);
			} break;
			default: {
				return 0;
			} break;
		}
	}

	size_t get_peregrine_hdr_size() const {
		return sizeof(peregrine_hdr_t);
	}

	peregrine_hdr_t* get_peregrine_hdr() const {
		auto l4_hdr = get_l4();
		auto l4_hdr_size = get_l4_size();

		if (l4_hdr_size == 0) {
			printf(
				"\n*** Not TCP/UDP/ICMP packet! Can't extract Peregrine "
				"header. ***\n");
			exit(1);
		}

		auto peregrine_hdr = (uint8_t*)l4_hdr.first + l4_hdr_size;
		return static_cast<peregrine_hdr_t*>((void*)peregrine_hdr);
	}

	void pretty_print() {
		auto eth_hdr = get_l2();
		auto ip_hdr = get_l3();
		auto l4_hdr = get_l4();
		auto peregrine_hdr = get_peregrine_hdr();

		printf("###[ Ethernet ]###\n");
		printf("  dst  %02x:%02x:%02x:%02x:%02x:%02x\n", eth_hdr->dst_mac[0],
			   eth_hdr->dst_mac[1], eth_hdr->dst_mac[2], eth_hdr->dst_mac[3],
			   eth_hdr->dst_mac[4], eth_hdr->dst_mac[5]);
		printf("  src  %02x:%02x:%02x:%02x:%02x:%02x\n", eth_hdr->src_mac[0],
			   eth_hdr->src_mac[1], eth_hdr->src_mac[2], eth_hdr->src_mac[3],
			   eth_hdr->src_mac[4], eth_hdr->src_mac[5]);
		printf("  type 0x%x\n", ntohs(eth_hdr->eth_type));

		printf("###[ IP ]###\n");
		printf("  ihl     %u\n", (ip_hdr->ihl & 0x0f));
		printf("  version %u\n", (ip_hdr->ihl & 0xf0) >> 4);
		printf("  tos     %u\n", ip_hdr->version);
		printf("  len     %u\n", ntohs(ip_hdr->tot_len));
		printf("  id      %u\n", ntohs(ip_hdr->id));
		printf("  off     %u\n", ntohs(ip_hdr->frag_off));
		printf("  ttl     %u\n", ip_hdr->ttl);
		printf("  proto   %u\n", ip_hdr->protocol);
		printf("  chksum  0x%x\n", ntohs(ip_hdr->check));
		printf("  src     %u.%u.%u.%u\n", (ip_hdr->src_ip >> 0) & 0xff,
			   (ip_hdr->src_ip >> 8) & 0xff, (ip_hdr->src_ip >> 16) & 0xff,
			   (ip_hdr->src_ip >> 24) & 0xff);
		printf("  dst     %u.%u.%u.%u\n", (ip_hdr->dst_ip >> 0) & 0xff,
			   (ip_hdr->dst_ip >> 8) & 0xff, (ip_hdr->dst_ip >> 16) & 0xff,
			   (ip_hdr->dst_ip >> 24) & 0xff);

		switch (l4_hdr.second) {
			case IP_PROTO_TCP: {
				auto tcp_hdr = static_cast<tcp_hdr_t*>(l4_hdr.first);
				printf("###[ TCP ]###\n");
				printf("  sport   %u\n", ntohs(tcp_hdr->src_port));
				printf("  dport   %u\n", ntohs(tcp_hdr->dst_port));
			} break;
			case IP_PROTO_UDP: {
				auto udp_hdr = static_cast<udp_hdr_t*>(l4_hdr.first);
				printf("###[ UDP ]###\n");
				printf("  sport   %u\n", ntohs(udp_hdr->src_port));
				printf("  dport   %u\n", ntohs(udp_hdr->dst_port));
			} break;
			case IP_PROTO_ICMP: {
				auto icmp_hdr = static_cast<icmp_hdr_t*>(l4_hdr.first);
				printf("###[ ICMP ]###\n");
				printf("  type    %u\n", icmp_hdr->type);
				printf("  code    %u\n", icmp_hdr->code);
			} break;
			default: {
				printf("\n*** Not TCP/UDP/ICMP packet! ***\n");
			} break;
		}

		printf("###[ Peregrine ]###\n");
		printf("  decay                   %u\n", ntohl(peregrine_hdr->decay));
		printf("  mac_ip_src_pkt_cnt      %u\n",
			   ntohl(peregrine_hdr->mac_ip_src_pkt_cnt));
		printf("  mac_ip_src_pkt_len      %u\n",
			   ntohl(peregrine_hdr->mac_ip_src_pkt_len));
		printf("  mac_ip_src_ss           %u\n",
			   ntohl(peregrine_hdr->mac_ip_src_ss));
		printf("  mac_ip_src_mean         %u\n",
			   ntohl(peregrine_hdr->mac_ip_src_mean));
		printf("  mac_ip_src_std_dev      %u\n",
			   ntohl(peregrine_hdr->mac_ip_src_std_dev));
		printf("  ip_src_pkt_cnt          %u\n",
			   ntohl(peregrine_hdr->ip_src_pkt_cnt));
		printf("  ip_src_pkt_len          %u\n",
			   ntohl(peregrine_hdr->ip_src_pkt_len));
		printf("  ip_src_ss               %u\n",
			   ntohl(peregrine_hdr->ip_src_ss));
		printf("  ip_src_mean             %u\n",
			   ntohl(peregrine_hdr->ip_src_mean));
		printf("  ip_src_std_dev          %u\n",
			   ntohl(peregrine_hdr->ip_src_std_dev));
		printf("  ip_pkt_cnt              %u\n",
			   ntohl(peregrine_hdr->ip_pkt_cnt));
		printf("  ip_ss_0                 %u\n", ntohl(peregrine_hdr->ip_ss_0));
		printf("  ip_ss_1                 %u\n", ntohl(peregrine_hdr->ip_ss_1));
		printf("  ip_mean_0               %u\n",
			   ntohl(peregrine_hdr->ip_mean_0));
		printf("  ip_pkt_cnt_1            %u\n",
			   ntohl(peregrine_hdr->ip_pkt_cnt_1));
		printf("  ip_mean_1               %u\n",
			   ntohl(peregrine_hdr->ip_mean_1));
		printf("  ip_std_dev_0            %u\n",
			   ntohl(peregrine_hdr->ip_std_dev_0));
		printf("  ip_magnitude            %u\n",
			   ntohl(peregrine_hdr->ip_magnitude));
		printf("  ip_radius               %u\n",
			   ntohl(peregrine_hdr->ip_radius));
		printf("  five_t_pkt_cnt          %u\n",
			   ntohl(peregrine_hdr->five_t_pkt_cnt));
		printf("  five_t_ss_0             %u\n",
			   ntohl(peregrine_hdr->five_t_ss_0));
		printf("  five_t_ss_1             %u\n",
			   ntohl(peregrine_hdr->five_t_ss_1));
		printf("  five_t_mean_0           %u\n",
			   ntohl(peregrine_hdr->five_t_mean_0));
		printf("  five_t_pkt_cnt_1        %u\n",
			   ntohl(peregrine_hdr->five_t_pkt_cnt_1));
		printf("  five_t_mean_1           %u\n",
			   ntohl(peregrine_hdr->five_t_mean_1));
		printf("  five_t_std_dev_0        %u\n",
			   ntohl(peregrine_hdr->five_t_std_dev_0));
		printf("  five_t_magnitude        %u\n",
			   ntohl(peregrine_hdr->five_t_magnitude));
		printf("  five_t_radius           %u\n",
			   ntohl(peregrine_hdr->five_t_radius));
		printf("  ip_sum_res_prod_cov     %lu\n",
			   peregrine_hdr->ip_sum_res_prod_cov);
		printf("  ip_pcc                  %lu\n", peregrine_hdr->ip_pcc);
		printf("  five_t_sum_res_prod_cov %lu\n",
			   peregrine_hdr->five_t_sum_res_prod_cov);
		printf("  five_t_pcc              %lu\n", peregrine_hdr->five_t_pcc);
	}
} __attribute__((packed));

};	// namespace peregrine