#pragma once

#include "tables/five_t_decay_check.h"
#include "tables/ip_mean_1_access.h"
#include "tables/ip_decay_check.h"
#include "tables/ip_mean.h"
#include "tables/ip_pkt_cnt_1_access.h"
#include "tables/ip_res_prod.h"
#include "tables/ip_res_struct_update.h"
#include "tables/ip_src_decay_check.h"
#include "tables/ip_src_mean.h"
#include "tables/ip_ss_1_access.h"
#include "tables/ip_sum_res_prod_get_carry.h"
#include "tables/mac_ip_src_decay_check.h"
#include "tables/mac_ip_src_mean.h"
#include "tables/ip_mean_ss_0.h"
#include "tables/ip_mean_ss_1.h"
#include "packet.h"

#ifdef __cplusplus
extern "C" {
#endif
#include <bf_rt/bf_rt_common.h>
#ifdef __cplusplus
}
#endif

namespace peregrine {

void init_bf_switchd();
void setup_controller();
void run(bool model);

struct bfrt_info_t;

class Controller {
public:
	static std::shared_ptr<Controller> controller;

private:
	std::shared_ptr<bfrt::BfRtSession> session;
	bf_rt_target_t dev_tgt;

	// Switch resources
	MacIpSrcDecayCheck mac_ip_src_decay_check;
	IpSrcDecayCheck ip_src_decay_check;
	IpDecayCheck ip_decay_check;
	FiveTDecayCheck five_t_decay_check;
	MacIpSrcMean mac_ip_src_mean;
	IpSrcMean ip_src_mean;
	IpMean ip_mean;
	IpResStructUpdate ip_res_struct_update;
	IpResProd ip_res_prod;
	IpSumResProdGetCarry ip_sum_res_prod_get_carry;
	IpPktCnt1Access ip_pkt_cnt_1_access;
	IpSs1Access ip_ss_1_access;
	IpMean1Access ip_mean_1_access;
	IpMeanSs0 ip_mean_ss_0;
	IpMeanSs1 ip_mean_ss_1;

	// statistics
	uint64_t pkts;

	Controller(const bfrt::BfRtInfo *_info,
			   std::shared_ptr<bfrt::BfRtSession> _session,
			   bf_rt_target_t _dev_tgt)
		: session(_session),
		  dev_tgt(_dev_tgt),
		  mac_ip_src_decay_check(_info, session, dev_tgt),
		  ip_src_decay_check(_info, session, dev_tgt),
		  ip_decay_check(_info, session, dev_tgt),
		  five_t_decay_check(_info, session, dev_tgt),
		  mac_ip_src_mean(_info, session, dev_tgt),
		  ip_src_mean(_info, session, dev_tgt),
		  ip_mean(_info, session, dev_tgt),
		  ip_res_struct_update(_info, session, dev_tgt),
		  ip_res_prod(_info, session, dev_tgt),
		  ip_sum_res_prod_get_carry(_info, session, dev_tgt),
		  ip_pkt_cnt_1_access(_info, session, dev_tgt),
		  ip_ss_1_access(_info, session, dev_tgt),
		  ip_mean_1_access(_info, session, dev_tgt),
		  ip_mean_ss_0(_info, session, dev_tgt),
		  ip_mean_ss_1(_info, session, dev_tgt) {
		// mac_ip_src_decay_check.dump();
		// ip_src_decay_check.dump();
		// ip_decay_check.dump();
		// five_t_decay_check.dump();
		// mac_ip_src_mean.dump();
		// ip_src_mean.dump();
		// ip_mean.dump();
		// ip_res_struct_update.dump();
		// ip_res_prod.dump();
		// ip_sum_res_prod_get_carry.dump();
		// ip_pkt_cnt_1_access.dump();
		// ip_ss_1_access.dump();
		// ip_mean_1_access.dump();
		ip_mean_ss_0.dump();
		ip_mean_ss_1.dump();
	}

public:
	Controller(Controller &other) = delete;
	void operator=(const Controller &) = delete;

	bool process(pkt_hdr_t *pkt_hdr);
	void dump_tables();

	std::shared_ptr<bfrt::BfRtSession> get_session() { return session; }
	bf_rt_target_t get_dev_tgt() const { return dev_tgt; }

	static void init(const bfrt::BfRtInfo *_info,
					 std::shared_ptr<bfrt::BfRtSession> _session,
					 bf_rt_target_t _dev_tgt);
};

}  // namespace peregrine