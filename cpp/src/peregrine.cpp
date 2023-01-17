#include "peregrine.h"

#include <bf_rt/bf_rt.hpp>

namespace peregrine {

std::shared_ptr<Controller> Controller::controller;

void Controller::init(const bfrt::BfRtInfo *info,
					  std::shared_ptr<bfrt::BfRtSession> session,
					  bf_rt_target_t dev_tgt) {
	if (controller) {
		return;
	}

	auto instance = new Controller(info, session, dev_tgt);
	controller = std::shared_ptr<Controller>(instance);
}

bool Controller::process(pkt_hdr_t *pkt_hdr) {
#ifdef DEBUG
	pkt_hdr->pretty_print();
#endif

	pkts++;
	session->sessionCompleteOperations();

	return true;
}

void Controller::dump_tables() {
	mac_ip_src_decay_check.dump();
}

}  // namespace peregrine
