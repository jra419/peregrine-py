#include <pcap.h>

#include <bf_rt/bf_rt.hpp>
#include <iostream>
#include <sstream>
#include <string>

#include "peregrine.h"

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
#define SDE_INSTALL_ENV_VAR "SDE_INSTALL"
#define PROGRAM_NAME "peregrine"

#define SWITCH_STATUS_SUCCESS 0x00000000L
#define SWITCH_STATUS_FAILURE 0x00000001L
#define SWITCH_PACKET_MAX_BUFFER_SIZE 10000
#define SWITCH_MEMCPY memcpy

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
	auto out_handle = (pcap_t *)args;
	auto pkt_hdr = (pkt_hdr_t *)packetData;

	assert(out_handle);
	assert(pkt_hdr);

	auto forward = Controller::controller->process(pkt_hdr);

	if (!forward) {
		return;
	}

	if (pcap_sendpacket(out_handle, packetData + sizeof(meta_hdr_t),
						pkthdr->caplen) != 0) {
		fprintf(stderr, "Error sending the packet: %s\n",
				pcap_geterr(out_handle));
		exit(2);
	}
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
	auto forward = Controller::controller->process(pkt_hdr);

	if (!forward) {
		bf_pkt_free(device, orig_pkt);
		return 0;
	}

	if (bf_pkt_data_copy(tx_pkt, (uint8_t *)in_packet + sizeof(meta_hdr_t),
						 packet_size - sizeof(meta_hdr_t)) != 0) {
		SWITCH_PKT_ERROR("bf_pkt_data_copy failed: pkt_size=%d\n", packet_size);
		bf_pkt_free(device, tx_pkt);
		return SWITCH_STATUS_FAILURE;
	}

	if (bf_pkt_tx(device, tx_pkt, tx_ring, (void *)tx_pkt) != BF_SUCCESS) {
		SWITCH_PKT_ERROR("bf_pkt_tx failed\n");
		bf_pkt_free(device, tx_pkt);
	}

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
	const char *in_dev = "veth251";
	const char *out_dev = "veth0";

	char errbuf[PCAP_ERRBUF_SIZE];

	pcap_t *in_handle;
	pcap_t *out_handle;

	in_handle = pcap_open_live(in_dev, BUFSIZ, true, 1000, errbuf);

	if (in_handle == nullptr) {
		fprintf(stderr, "Couldn't open device %s: %s\n", in_dev, errbuf);
		exit(2);
	}

	out_handle = pcap_open_live(out_dev, BUFSIZ, true, 1000, errbuf);

	if (out_handle == NULL) {
		fprintf(stderr, "Couldn't open device %s: %s\n", out_dev, errbuf);
		exit(2);
	}

	pcap_setdirection(in_handle, PCAP_D_IN);
	pcap_loop(in_handle, -1, pcap_callback_func, (u_char *)out_handle);

	pcap_setdirection(in_handle, PCAP_D_IN);

	return nullptr;
}

char *get_install_dir() {
	auto install_dir = getenv(SDE_INSTALL_ENV_VAR);

	if (!install_dir) {
		std::cerr << SDE_INSTALL_ENV_VAR << " env var not found.\n";
		exit(1);
	}

	return getenv(SDE_INSTALL_ENV_VAR);
}

std::string get_target_conf_file() {
	std::stringstream ss;

	ss << get_install_dir();
	ss << "/share/p4/targets/tofino/";
	ss << PROGRAM_NAME << ".conf";

	return ss.str();
}

void init_bf_switchd() {
	auto switchd_main_ctx =
		(bf_switchd_context_t *)calloc(1, sizeof(bf_switchd_context_t));

	/* Allocate memory to hold switchd configuration and state */
	if (switchd_main_ctx == NULL) {
		std::cerr << "ERROR: Failed to allocate memory for switchd context\n";
		return;
	}

	auto target_conf_file = get_target_conf_file();

	memset(switchd_main_ctx, 0, sizeof(bf_switchd_context_t));

	switchd_main_ctx->install_dir = get_install_dir();
	switchd_main_ctx->conf_file = const_cast<char *>(target_conf_file.c_str());
	switchd_main_ctx->skip_p4 = false;
	switchd_main_ctx->skip_port_add = false;
	switchd_main_ctx->running_in_background = true;
	switchd_main_ctx->dev_sts_thread = true;
	switchd_main_ctx->dev_sts_port = THRIFT_PORT_NUM;

	auto bf_status = bf_switchd_lib_init(switchd_main_ctx);
	std::cerr << "Initialized bf_switchd, status = " << bf_status << "\n";

	if (bf_status != BF_SUCCESS) {
		exit(1);
	}
}

void setup_controller() {
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

	// Ports ports(info, session, dev_tgt);
	// ports.add_port(LAN, 0, BF_SPEED_100G);
	// ports.add_port(WAN, 0, BF_SPEED_100G);

	Controller::init(info, session, dev_tgt);

	std::cerr << "Controller setup done!\n";
}

void run(bool model) {
	std::cerr << "NF main learning thread started...\n";

	if (model) {
		pthread_create(&ether_if_sniff_thread, nullptr,
					   register_ethernet_pkt_ops, nullptr);
		ether_sniff_thread_launched = true;
	} else {
		auto dev_tgt = Controller::controller->get_dev_tgt();
		register_pcie_pkt_ops(dev_tgt);
	}
}

}  // namespace peregrine