#pragma once

#include "packet.h"
#include "table.h"

namespace peregrine {

class IpPktCnt1Access : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t pkt_cnt_global;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t pkt_cnt_1_incr;
		bf_rt_id_t pkt_cnt_1_read;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpPktCnt1Access(const bfrt::BfRtInfo *info,
					std::shared_ptr<bfrt::BfRtSession> session,
					const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.stats_ip_a.pkt_cnt_1_access") {
		init_key({
			{"ig_md.meta.pkt_cnt_global", &key_fields.pkt_cnt_global},
		});

		init_actions({
			{"SwitchIngress_a.stats_ip_a.pkt_cnt_1_incr",
			 &actions.pkt_cnt_1_incr},
			{"SwitchIngress_a.stats_ip_a.pkt_cnt_1_read",
			 &actions.pkt_cnt_1_read},
		});

		// fill mac ip src decay check table
		add_entry(0b00000000000000000000000000000000,
				  0b11111111111111111111111111111111, actions.pkt_cnt_1_incr);
		add_entry(0b11111111111111111111110000000000,
				  0b00000000000000000000001111111111, actions.pkt_cnt_1_read);
		add_entry(0b11111111111111111111111111111111,
				  0b00000000000000000000000000000000, actions.pkt_cnt_1_incr);
	}

private:
	void add_entry(uint32_t value, uint32_t mask, bf_rt_id_t action_id) {
		key_setup(value, mask);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t value, uint32_t mask) {
		table->keyReset(key.get());
		auto bf_status = key->setValueandMask(key_fields.pkt_cnt_global,
											  static_cast<uint64_t>(value),
											  static_cast<uint64_t>(mask));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine