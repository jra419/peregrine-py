#pragma once

#include "../table.h"

namespace peregrine {

class FiveTPcc : public Table {
private:
	static constexpr uint32_t NUM_ACTIONS = 32;

	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t std_dev_prod;
		bf_rt_id_t priority;
	};

	struct actions_t {
		// Actions ids
		std::vector<bf_rt_id_t> rshift_pccs;

		actions_t() : rshift_pccs(NUM_ACTIONS) {}
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	FiveTPcc(const bfrt::BfRtInfo *info,
			  std::shared_ptr<bfrt::BfRtSession> session,
			  const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchIngress_b.stats_five_t_b.pcc") {
		init_key({
			{"ig_md.stats_five_t.std_dev_prod", &key_fields.std_dev_prod},
			{"$MATCH_PRIORITY", &key_fields.priority},
		});

		auto actions_to_init = std::unordered_map<std::string, bf_rt_id_t *>();

		for (auto i = 0u; i < NUM_ACTIONS; i++) {
			std::stringstream ss;
			ss << "SwitchIngress_b.stats_five_t_b.rshift_pcc_";
			ss << i;

			auto action_name = ss.str();
			auto *action_id = &actions.rshift_pccs[i];

			actions_to_init[action_name] = action_id;
		}

		init_actions(actions_to_init);

		// fill up table
		for (auto i = 0u; i < NUM_ACTIONS; i++) {
			uint32_t priority = NUM_ACTIONS - i;
			uint32_t power = 1 << i;
			uint32_t mask = 0xffffffff << i;
			auto action_id = actions.rshift_pccs[i];
			add_entry(priority, power, mask, action_id);
		}
	}

private:
	void add_entry(uint32_t priority, uint32_t power, uint32_t mask,
				   bf_rt_id_t action_id) {
		key_setup(priority, power, mask);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t priority, uint32_t power, uint32_t mask) {
		table->keyReset(key.get());

		auto bf_status = key->setValueandMask(key_fields.std_dev_prod,
											  static_cast<uint64_t>(power),
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