#pragma once

#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>

namespace peregrine {

typedef uint8_t mac_t[6];
typedef uint32_t ipv4_t;
typedef uint16_t port_t;

struct eth_hdr_t {
	mac_t dst_mac;
	mac_t src_mac;
	uint16_t eth_type;
} __attribute__((packed));

struct meta_hdr_t {
	port_t public_port;
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

struct tcpudp_hdr_t {
	port_t src_port;
	port_t dst_port;
} __attribute__((packed));

struct pkt_hdr_t {
	struct meta_hdr_t meta_hdr;
	struct eth_hdr_t eth_hdr;
	struct ipv4_hdr_t ip_hdr;
	struct tcpudp_hdr_t tcpudp_hdr;

	void pretty_print() {
		printf("###[ Meta ]###\n");
		printf("  port   %u\n", ntohs(meta_hdr.public_port));

		printf("###[ Ethernet ]###\n");
		printf("  dst  %02x:%02x:%02x:%02x:%02x:%02x\n", eth_hdr.dst_mac[0],
			   eth_hdr.dst_mac[1], eth_hdr.dst_mac[2], eth_hdr.dst_mac[3],
			   eth_hdr.dst_mac[4], eth_hdr.dst_mac[5]);
		printf("  src  %02x:%02x:%02x:%02x:%02x:%02x\n", eth_hdr.src_mac[0],
			   eth_hdr.src_mac[1], eth_hdr.src_mac[2], eth_hdr.src_mac[3],
			   eth_hdr.src_mac[4], eth_hdr.src_mac[5]);
		printf("  type 0x%x\n", ntohs(eth_hdr.eth_type));

		printf("###[ IP ]###\n");
		printf("  ihl     %u\n", (ip_hdr.ihl & 0x0f));
		printf("  version %u\n", (ip_hdr.ihl & 0xf0) >> 4);
		printf("  tos     %u\n", ip_hdr.version);
		printf("  len     %u\n", ntohs(ip_hdr.tot_len));
		printf("  id      %u\n", ntohs(ip_hdr.id));
		printf("  off     %u\n", ntohs(ip_hdr.frag_off));
		printf("  ttl     %u\n", ip_hdr.ttl);
		printf("  proto   %u\n", ip_hdr.protocol);
		printf("  chksum  0x%x\n", ntohs(ip_hdr.check));
		printf("  src     %u.%u.%u.%u\n", (ip_hdr.src_ip >> 0) & 0xff,
			   (ip_hdr.src_ip >> 8) & 0xff, (ip_hdr.src_ip >> 16) & 0xff,
			   (ip_hdr.src_ip >> 24) & 0xff);
		printf("  dst     %u.%u.%u.%u\n", (ip_hdr.dst_ip >> 0) & 0xff,
			   (ip_hdr.dst_ip >> 8) & 0xff, (ip_hdr.dst_ip >> 16) & 0xff,
			   (ip_hdr.dst_ip >> 24) & 0xff);

		printf("###[ TCP/UDP ]###\n");
		printf("  sport   %u\n", ntohs(tcpudp_hdr.src_port));
		printf("  dport   %u\n", ntohs(tcpudp_hdr.dst_port));
	}
} __attribute__((packed));

};	// namespace peregrine