#pragma once

#include "../table.h"

namespace peregrine {

class IpSrcDecayCheck : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t decay_cntr;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t decay_check_100_ms;
		bf_rt_id_t decay_check_1_s;
		bf_rt_id_t decay_check_10_s;
		bf_rt_id_t decay_check_60_s;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpSrcDecayCheck(const bfrt::BfRtInfo *info,
					   std::shared_ptr<bfrt::BfRtSession> session,
					   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.stats_ip_src_a.decay_check") {
		init_key({
			{"ig_md.meta.decay_cntr", &key_fields.decay_cntr},
		});

		init_actions({
			{"SwitchIngress_a.stats_ip_src_a.decay_check_100_ms",
			 &actions.decay_check_100_ms},
			{"SwitchIngress_a.stats_ip_src_a.decay_check_1_s",
			 &actions.decay_check_1_s},
			{"SwitchIngress_a.stats_ip_src_a.decay_check_10_s",
			 &actions.decay_check_10_s},
			{"SwitchIngress_a.stats_ip_src_a.decay_check_60_s",
			 &actions.decay_check_60_s},
		});

		// fill up table
		add_entry(0, actions.decay_check_100_ms);
		add_entry(8192, actions.decay_check_1_s);
		add_entry(16384, actions.decay_check_10_s);
		add_entry(24576, actions.decay_check_60_s);
	}

private:
	void add_entry(uint32_t counter, bf_rt_id_t action_id) {
		key_setup(counter);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t counter) {
		table->keyReset(key.get());
		auto bf_status = key->setValue(key_fields.decay_cntr,
									   static_cast<uint64_t>(counter));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine