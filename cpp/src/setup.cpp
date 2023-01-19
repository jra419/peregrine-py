#include <pcap.h>

#include <bf_rt/bf_rt.hpp>
#include <iostream>
#include <sstream>
#include <string>

#include "peregrine.h"
#include "ports.h"

#ifdef __cplusplus
extern "C" {
#endif
#include <bf_rt/bf_rt_common.h>
#include <bf_switchd/bf_switchd.h>
#include <bfutils/bf_utils.h>  // required for bfshell
#include <pkt_mgr/pkt_mgr_intf.h>
#ifdef __cplusplus
}
#endif

#define THRIFT_PORT_NUM 7777
#define ALL_PIPES 0xffff

#define ENV_VAR_SDE_INSTALL "SDE_INSTALL"
#define ENV_VAR_CONF_FILE "PEREGRINE_HW_CONF"
#define PROGRAM_NAME "peregrine"

#define SWITCH_STATUS_SUCCESS 0x00000000L
#define SWITCH_STATUS_FAILURE 0x00000001L
#define SWITCH_PACKET_MAX_BUFFER_SIZE 10000
#define SWITCH_MEMCPY memcpy

#define IN_VIRTUAL_IFACE "veth251"

#define CPU_PORT_TOFINO_MODEL 64

#define BFN_T10_032D_CONF_FILE "../../confs/BFN-T10-032D.conf"

// BFN-T10-032D
// BFN-T10-032D-024
// BFN-T10-032D-020
// BFN-T10-032D-018
#define CPU_PORT_2_PIPES 192

// BFN-T10-064Q
// BFN-T10-032Q
#define CPU_PORT_4_PIPES 192

#define SWITCH_PKT_ERROR(fmt, arg...)                                 \
	bf_sys_log_and_trace(BF_MOD_SWITCHAPI, BF_LOG_ERR, "%s:%d: " fmt, \
						 __FUNCTION__, __LINE__, ##arg)
#define SWITCH_PKT_DEBUG(fmt, arg...)                                \
	bf_sys_log_and_trace(BF_MOD_SWITCHAPI, BF_LOG_DBG, "%s:%d " fmt, \
						 __FUNCTION__, __LINE__, ##arg)

namespace peregrine {

typedef int switch_int32_t;
typedef uint32_t switch_status_t;

pthread_t nf_main_thread;
pthread_t ether_if_sniff_thread;
bool ether_sniff_thread_launched;

bf_pkt *tx_pkt = nullptr;
bf_pkt_tx_ring_t tx_ring = BF_PKT_TX_RING_0;

void pcap_callback_func(u_char *args, const struct pcap_pkthdr *pkthdr,
						const u_char *packetData) {
	auto pkt_hdr = (pkt_hdr_t *)packetData;
	assert(pkt_hdr);
	Controller::controller->process(pkt_hdr);
}

bf_status_t pcie_tx(bf_dev_id_t device, bf_pkt_tx_ring_t tx_ring,
					uint64_t tx_cookie, uint32_t status) {
	return BF_SUCCESS;
}

bf_status_t pcie_rx(bf_dev_id_t device, bf_pkt *pkt, void *data,
					bf_pkt_rx_ring_t rx_ring) {
	bf_pkt *orig_pkt = nullptr;
	char in_packet[SWITCH_PACKET_MAX_BUFFER_SIZE];
	char *pkt_buf = nullptr;
	char *bufp = nullptr;
	uint32_t packet_size = 0;
	switch_int32_t pkt_len = 0;
	switch_status_t status = SWITCH_STATUS_SUCCESS;

	// save a pointer to the packet
	orig_pkt = pkt;

	// assemble the received packet
	bufp = &in_packet[0];

	do {
		pkt_buf = (char *)bf_pkt_get_pkt_data(pkt);
		pkt_len = bf_pkt_get_pkt_size(pkt);
		if ((packet_size + pkt_len) > SWITCH_PACKET_MAX_BUFFER_SIZE) {
			SWITCH_PKT_ERROR("Packet too large to Transmit - SKipping\n");
			break;
		}
		SWITCH_MEMCPY(bufp, pkt_buf, pkt_len);
		bufp += pkt_len;
		packet_size += pkt_len;
		pkt = bf_pkt_get_nextseg(pkt);
	} while (pkt);

	pkt_hdr_t *pkt_hdr = (pkt_hdr_t *)in_packet;
	Controller::controller->process(pkt_hdr);

	bf_pkt_free(device, orig_pkt);
	return 0;
}

void register_pcie_pkt_ops(bf_rt_target_t dev_tgt) {
	int tx_ring;
	int rx_ring;
	bf_status_t status;

	// register callback for TX complete
	for (tx_ring = BF_PKT_TX_RING_0; tx_ring < BF_PKT_TX_RING_MAX; tx_ring++) {
		bf_pkt_tx_done_notif_register(dev_tgt.dev_id, pcie_tx,
									  (bf_pkt_tx_ring_t)tx_ring);
	}

	// register callback for RX
	for (rx_ring = BF_PKT_RX_RING_0; rx_ring < BF_PKT_RX_RING_MAX; rx_ring++) {
		status = bf_pkt_rx_register(dev_tgt.dev_id, pcie_rx,
									(bf_pkt_rx_ring_t)rx_ring, 0);
	}
}

void *register_ethernet_pkt_ops(void *args) {
	char errbuf[PCAP_ERRBUF_SIZE];
	auto in_handle =
		pcap_open_live(IN_VIRTUAL_IFACE, BUFSIZ, true, 1000, errbuf);

	if (in_handle == nullptr) {
		fprintf(stderr, "Couldn't open device %s: %s\n", IN_VIRTUAL_IFACE,
				errbuf);
		exit(2);
	}

	pcap_setdirection(in_handle, PCAP_D_IN);
	pcap_loop(in_handle, -1, pcap_callback_func, nullptr);

	return nullptr;
}

char* get_env_var_value(const char* env_var) {
	auto env_var_value = getenv(env_var);

	if (!env_var_value) {
		std::cerr << env_var << " env var not found.\n";
		exit(1);
	}

	return env_var_value;
}

char *get_install_dir() {
	return get_env_var_value(ENV_VAR_SDE_INSTALL);
}

std::string get_target_conf_file() {
	return get_env_var_value(ENV_VAR_CONF_FILE);
}

void init_bf_switchd(bool use_tofino_model) {
	auto switchd_main_ctx =
		(bf_switchd_context_t *)calloc(1, sizeof(bf_switchd_context_t));

	/* Allocate memory to hold switchd configuration and state */
	if (switchd_main_ctx == NULL) {
		std::cerr << "ERROR: Failed to allocate memory for switchd context\n";
		exit(1);
	}

	auto target_conf_file = get_target_conf_file();

	memset(switchd_main_ctx, 0, sizeof(bf_switchd_context_t));

	switchd_main_ctx->install_dir = get_install_dir();
	switchd_main_ctx->conf_file = const_cast<char *>(target_conf_file.c_str());
	switchd_main_ctx->skip_p4 = false;
	switchd_main_ctx->skip_port_add = false;
	switchd_main_ctx->running_in_background = use_tofino_model;
	switchd_main_ctx->dev_sts_thread = true;
	switchd_main_ctx->dev_sts_port = THRIFT_PORT_NUM;

	auto bf_status = bf_switchd_lib_init(switchd_main_ctx);
	std::cerr << "Initialized bf_switchd, status = " << bf_status << "\n";

	if (bf_status != BF_SUCCESS) {
		exit(1);
	}
}

void configure_ports(const bfrt::BfRtInfo *info,
					 std::shared_ptr<bfrt::BfRtSession> session,
					 bf_rt_target_t dev_tgt, Ports& ports, const topology_t &topology) {
	for (auto connection : topology.connections) {
		auto in_speed = Ports::gbps_to_bf_port_speed(connection.in.capacity);
		auto out_speed = Ports::gbps_to_bf_port_speed(connection.out.capacity);

		ports.add_port(connection.in.port, 0, in_speed);
		ports.add_port(connection.out.port, 0, out_speed);
	}
}

void setup_controller(const std::string &topology_file_path, bool use_tofino_model) {
	auto topology = parse_topology_file(topology_file_path);
	setup_controller(topology, use_tofino_model);
}

void configure_cpu_port(Ports& ports, bool use_tofino_model) {
	auto cpu_port = use_tofino_model ? CPU_PORT_TOFINO_MODEL : CPU_PORT_2_PIPES;
	cpu_port = use_tofino_model ? cpu_port : ports.get_dev_port(cpu_port, 0);
	p4_devport_mgr_set_copy_to_cpu(0, true, cpu_port);
}

void setup_controller(const topology_t &topology, bool use_tofino_model) {
	bf_rt_target_t dev_tgt;
	dev_tgt.dev_id = 0;
	dev_tgt.pipe_id = ALL_PIPES;

	// Get devMgr singleton instance
	auto &devMgr = bfrt::BfRtDevMgr::getInstance();

	// Get info object from dev_id and p4 program name
	const bfrt::BfRtInfo *info = nullptr;
	auto bf_status = devMgr.bfRtInfoGet(dev_tgt.dev_id, PROGRAM_NAME, &info);

	if (bf_pkt_alloc(dev_tgt.dev_id, &tx_pkt, 1500,
					 BF_DMA_CPU_PKT_TRANSMIT_0) != 0) {
		std::cerr << "Failed to allocate packet buffer\n";
		exit(1);
	}

	// Create a session object
	auto session = bfrt::BfRtSession::sessionCreate();

	Ports ports(info, session, dev_tgt);

	configure_cpu_port(ports, use_tofino_model);

	if (!use_tofino_model) {
		configure_ports(info, session, dev_tgt, ports, topology);
	}

	Controller::init(info, session, dev_tgt, ports, topology, use_tofino_model);
}

void run(bool use_tofino_model) {
	std::cerr << "NF main learning thread started...\n";

	if (use_tofino_model) {
		pthread_create(&ether_if_sniff_thread, nullptr,
					   register_ethernet_pkt_ops, nullptr);
		ether_sniff_thread_launched = true;
	} else {
		auto dev_tgt = Controller::controller->get_dev_tgt();
		register_pcie_pkt_ops(dev_tgt);
	}
}

}  // namespace peregrine