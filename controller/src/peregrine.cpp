#include "peregrine.h"
#include "ports.h"

#include <bf_rt/bf_rt.hpp>

namespace peregrine {

std::shared_ptr<Controller> Controller::controller;

void Controller::configure_ports(const topology_t &topology) {
	auto stats_speed = Ports::gbps_to_bf_port_speed(topology.stats.capacity);
	ports.add_port(topology.stats.port, 0, stats_speed);

	for (auto connection : topology.connections) {
		auto in_speed = Ports::gbps_to_bf_port_speed(connection.in.capacity);
		auto out_speed = Ports::gbps_to_bf_port_speed(connection.out.capacity);

		ports.add_port(connection.in.port, 0, in_speed);
		ports.add_port(connection.out.port, 0, out_speed);
	}
}

void Controller::configure_stats_port(uint16_t stats_port,
									  bool use_tofino_model) {
	if (!use_tofino_model) {
		stats_port = ports.get_dev_port(stats_port, 0);
	}

	p4_devport_mgr_set_copy_to_cpu(0, true, stats_port);
}

void Controller::init(const bfrt::BfRtInfo *info,
					  std::shared_ptr<bfrt::BfRtSession> session,
					  bf_rt_target_t dev_tgt, const topology_t &topology,
					  bool use_tofino_model) {
	if (controller) {
		return;
	}

	auto instance =
		new Controller(info, session, dev_tgt, topology, use_tofino_model);
	controller = std::shared_ptr<Controller>(instance);
}

bool Controller::process(pkt_hdr_t *pkt_hdr) {
#ifdef DEBUG
	pkt_hdr->pretty_print();
#endif

	session->sessionCompleteOperations();

	return true;
}

}  // namespace peregrine
