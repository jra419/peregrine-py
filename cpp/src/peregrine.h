#pragma once

#include <algorithm>

#include "packet.h"
#include "tables/five_t_cov.h"
#include "tables/five_t_decay_check.h"
#include "tables/five_t_mean_0.h"
#include "tables/five_t_mean_1_access.h"
#include "tables/five_t_mean_ss_0.h"
#include "tables/five_t_mean_ss_1.h"
#include "tables/five_t_pcc.h"
#include "tables/five_t_pkt_cnt_1_access.h"
#include "tables/five_t_res_prod.h"
#include "tables/five_t_res_struct_update.h"
#include "tables/five_t_ss_1_access.h"
#include "tables/five_t_std_dev_prod.h"
#include "tables/five_t_sum_res_prod_get_carry.h"
#include "tables/five_t_variance_0_abs.h"
#include "tables/five_t_variance_1_abs.h"
#include "tables/fwd_recirculation_a.h"
#include "tables/fwd_recirculation_b.h"
#include "tables/ip_cov.h"
#include "tables/ip_decay_check.h"
#include "tables/ip_mean_0.h"
#include "tables/ip_mean_1_access.h"
#include "tables/ip_mean_ss_0.h"
#include "tables/ip_mean_ss_1.h"
#include "tables/ip_pcc.h"
#include "tables/ip_pkt_cnt_1_access.h"
#include "tables/ip_res_prod.h"
#include "tables/ip_res_struct_update.h"
#include "tables/ip_src_decay_check.h"
#include "tables/ip_src_mean.h"
#include "tables/ip_ss_1_access.h"
#include "tables/ip_std_dev_prod.h"
#include "tables/ip_sum_res_prod_get_carry.h"
#include "tables/ip_variance_0_abs.h"
#include "tables/ip_variance_1_abs.h"
#include "tables/mac_ip_src_decay_check.h"
#include "tables/mac_ip_src_mean.h"
#include "topology.h"
#include "ports.h"

#ifdef __cplusplus
extern "C" {
#endif
#include <bf_rt/bf_rt_common.h>
#ifdef __cplusplus
}
#endif

namespace peregrine {

void init_bf_switchd();
void setup_controller(const topology_t &topology, bool model);
void setup_controller(const std::string &topology_file_path, bool model);
void run(bool model);

struct bfrt_info_t;

class Controller {
public:
	static std::shared_ptr<Controller> controller;

private:
	const bfrt::BfRtInfo *info;
	std::shared_ptr<bfrt::BfRtSession> session;
	bf_rt_target_t dev_tgt;

	// Switch resources
	MacIpSrcDecayCheck mac_ip_src_decay_check;
	IpSrcDecayCheck ip_src_decay_check;
	IpDecayCheck ip_decay_check;
	FiveTDecayCheck five_t_decay_check;
	MacIpSrcMean mac_ip_src_mean;
	IpSrcMean ip_src_mean;
	IpMean0 ip_mean_0;
	IpResStructUpdate ip_res_struct_update;
	IpResProd ip_res_prod;
	IpSumResProdGetCarry ip_sum_res_prod_get_carry;
	IpPktCnt1Access ip_pkt_cnt_1_access;
	IpSs1Access ip_ss_1_access;
	IpMean1Access ip_mean_1_access;
	IpMeanSs0 ip_mean_ss_0;
	IpMeanSs1 ip_mean_ss_1;
	IpVariance0Abs ip_variance_0_abs;
	IpVariance1Abs ip_variance_1_abs;
	IpCov ip_cov;
	IpStdDevProd ip_std_dev_prod;
	IpPcc ip_pcc;
	FiveTMean0 five_t_mean_0;
	FiveTResStructUpdate five_t_res_struct_update;
	FiveTResProd five_t_res_prod;
	FiveTSumResProdGetCarry five_t_sum_res_prod_get_carry;
	FiveTPktCnt1Access five_t_pkt_cnt_1_access;
	FiveTSs1Access five_t_ss_1_access;
	FiveTMean1Access five_t_mean_1_access;
	FiveTMeanSs0 five_t_mean_ss_0;
	FiveTMeanSs1 five_t_mean_ss_1;
	FiveTVariance0Abs five_t_variance_0_abs;
	FiveTVariance1Abs five_t_variance_1_abs;
	FiveTCov five_t_cov;
	FiveTStdDevProd five_t_std_dev_prod;
	FiveTPcc five_t_pcc;
	FwdRecirculation_a fwd_recirculation_a;
	FwdRecirculation_b fwd_recirculation_b;

	// statistics
	uint64_t pkts;

	Controller(const bfrt::BfRtInfo *_info,
			   std::shared_ptr<bfrt::BfRtSession> _session,
			   bf_rt_target_t _dev_tgt, Ports &ports,
			   const topology_t &topology, bool model)
		: info(_info),
		  session(_session),
		  dev_tgt(_dev_tgt),
		  mac_ip_src_decay_check(_info, session, dev_tgt),
		  ip_src_decay_check(_info, session, dev_tgt),
		  ip_decay_check(_info, session, dev_tgt),
		  five_t_decay_check(_info, session, dev_tgt),
		  mac_ip_src_mean(_info, session, dev_tgt),
		  ip_src_mean(_info, session, dev_tgt),
		  ip_mean_0(_info, session, dev_tgt),
		  ip_res_struct_update(_info, session, dev_tgt),
		  ip_res_prod(_info, session, dev_tgt),
		  ip_sum_res_prod_get_carry(_info, session, dev_tgt),
		  ip_pkt_cnt_1_access(_info, session, dev_tgt),
		  ip_ss_1_access(_info, session, dev_tgt),
		  ip_mean_1_access(_info, session, dev_tgt),
		  ip_mean_ss_0(_info, session, dev_tgt),
		  ip_mean_ss_1(_info, session, dev_tgt),
		  ip_variance_0_abs(_info, session, dev_tgt),
		  ip_variance_1_abs(_info, session, dev_tgt),
		  ip_cov(_info, session, dev_tgt),
		  ip_std_dev_prod(_info, session, dev_tgt),
		  ip_pcc(_info, session, dev_tgt),
		  five_t_mean_0(_info, session, dev_tgt),
		  five_t_res_struct_update(_info, session, dev_tgt),
		  five_t_res_prod(_info, session, dev_tgt),
		  five_t_sum_res_prod_get_carry(_info, session, dev_tgt),
		  five_t_pkt_cnt_1_access(_info, session, dev_tgt),
		  five_t_ss_1_access(_info, session, dev_tgt),
		  five_t_mean_1_access(_info, session, dev_tgt),
		  five_t_mean_ss_0(_info, session, dev_tgt),
		  five_t_mean_ss_1(_info, session, dev_tgt),
		  five_t_variance_0_abs(_info, session, dev_tgt),
		  five_t_variance_1_abs(_info, session, dev_tgt),
		  five_t_cov(_info, session, dev_tgt),
		  five_t_std_dev_prod(_info, session, dev_tgt),
		  five_t_pcc(_info, session, dev_tgt),
		  fwd_recirculation_a(_info, session, dev_tgt),
		  fwd_recirculation_b(_info, session, dev_tgt) {
		for (auto connection : topology.connections) {
			auto ig_port = connection.in.port;
			auto eg_port = connection.out.port;

			// Use an internal port in another pipe.
			// Method to choose which port: just use the same port but on
			// another pipe.
			auto ig_local_port = ig_port & 0x7F;
			auto ig_pipe = (ig_port >> 7) & 0x3;

			auto found_it = std::find(topology.pipes.external.begin(),
									  topology.pipes.external.end(), ig_pipe);
			assert(found_it != topology.pipes.external.end());
			auto index = found_it - topology.pipes.external.begin();
			auto internal_pipe = topology.pipes.internal[index];

			auto internal_port = (internal_pipe << 7) | ig_port;

			if (!model) {
				ig_port = ports.get_dev_port(ig_port, 0);
				eg_port = ports.get_dev_port(eg_port, 0);
			}

			fwd_recirculation_a.add_entry(ig_port, internal_port);
			fwd_recirculation_b.add_entry(internal_port, eg_port);
		}
	}

public:
	Controller(Controller &other) = delete;
	void operator=(const Controller &) = delete;

	bool process(pkt_hdr_t *pkt_hdr);

	const bfrt::BfRtInfo *get_info() const { return info; }
	std::shared_ptr<bfrt::BfRtSession> get_session() { return session; }
	bf_rt_target_t get_dev_tgt() const { return dev_tgt; }

	static void init(const bfrt::BfRtInfo *_info,
					 std::shared_ptr<bfrt::BfRtSession> _session,
					 bf_rt_target_t _dev_tgt, Ports &ports,
					 const topology_t &topology, bool model);
};

}  // namespace peregrine