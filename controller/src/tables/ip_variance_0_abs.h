#pragma once

#include "../table.h"

namespace peregrine {

class IpVariance0Abs : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t variance_0;
		bf_rt_id_t priority;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t variance_0_pos;
		bf_rt_id_t variance_0_neg;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpVariance0Abs(const bfrt::BfRtInfo *info,
				   std::shared_ptr<bfrt::BfRtSession> session,
				   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_b.stats_ip_b.variance_0_abs") {
		init_key({
			{"ig_md.stats_ip.variance_0", &key_fields.variance_0},
			{"$MATCH_PRIORITY", &key_fields.priority},
		});

		init_actions({
			{"SwitchIngress_b.stats_ip_b.variance_0_pos",
			 &actions.variance_0_pos},
			{"SwitchIngress_b.stats_ip_b.variance_0_neg",
			 &actions.variance_0_neg},
		});

		// fill up table
		add_entry(2, 0b00000000000000000000000000000000,
				  0b10000000000000000000000000000000, actions.variance_0_pos);
		add_entry(1, 0b10000000000000000000000000000000,
				  0b10000000000000000000000000000000, actions.variance_0_neg);
	}

private:
	void add_entry(uint32_t priority, uint32_t value, uint32_t mask, bf_rt_id_t action_id) {
		key_setup(priority, value, mask);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t priority, uint32_t value, uint32_t mask) {
		table->keyReset(key.get());
		
		auto bf_status = key->setValueandMask(key_fields.variance_0,
											  static_cast<uint64_t>(value),
											  static_cast<uint64_t>(mask));
		assert(bf_status == BF_SUCCESS);

		bf_status =
			key->setValue(key_fields.priority, static_cast<uint64_t>(priority));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine