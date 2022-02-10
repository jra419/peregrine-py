#ifndef _CONSTANTS_
#define _CONSTANTS_

#define MAX_PORTS 255

typedef bit<16> ether_type_t;
const ether_type_t ETHERTYPE_IPV4 = 16w0x0800;

typedef bit<8> ip_proto_t;
const ip_proto_t IP_PROTO_ICMP = 1;
const ip_proto_t IP_PROTO_IPV4 = 4;
const ip_proto_t IP_PROTO_TCP = 6;
const ip_proto_t IP_PROTO_UDP = 17;

typedef bit<9> port_t;

const port_t CPU_PORT = 255;

#define DECAY_100_MS 1525
#define DECAY_1_S 15258
#define DECAY_10_S 152587
#define DECAY_60_S 915527

#define REG_SIZE 32768

#endif
