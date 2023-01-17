#pragma once

#include "../table.h"

namespace peregrine {

class IpResProd : public Table {
private:
	static constexpr uint32_t NUM_ACTIONS = 30;

	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t res_1;
	};

	struct actions_t {
		// Actions ids
		std::vector<bf_rt_id_t> lshift_res_prod;

		actions_t() : lshift_res_prod(NUM_ACTIONS) {}
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpResProd(const bfrt::BfRtInfo *info,
			  std::shared_ptr<bfrt::BfRtSession> session,
			  const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchIngress_a.stats_ip_a.res_prod") {
		init_key({
			{"ig_md.stats_ip.res_1", &key_fields.res_1},
		});

		auto actions_to_init = std::unordered_map<std::string, bf_rt_id_t *>();

		for (auto i = 0u; i < NUM_ACTIONS; i++) {
			std::stringstream ss;
			ss << "SwitchIngress_a.stats_ip_a.lshift_res_prod_";
			ss << i;

			auto action_name = ss.str();
			auto *action_id = &actions.lshift_res_prod[i];

			actions_to_init[action_name] = action_id;
		}

		init_actions(actions_to_init);

		// fill up table
		for (auto i = 0u; i < NUM_ACTIONS; i++) {
			uint32_t power = 1 << i;
			uint32_t mask = 0xffffffff << i;
			auto action_id = actions.lshift_res_prod[i];
			add_entry(power, mask, action_id);
		}
	}

private:
	void add_entry(uint32_t power, uint32_t mask, bf_rt_id_t action_id) {
		key_setup(power, mask);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t power, uint32_t mask) {
		table->keyReset(key.get());
		auto bf_status = key->setValueandMask(key_fields.res_1,
											  static_cast<uint64_t>(power),
											  static_cast<uint64_t>(mask));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine