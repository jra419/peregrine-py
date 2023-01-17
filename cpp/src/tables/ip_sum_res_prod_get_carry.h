#pragma once

#include "../table.h"

namespace peregrine {

class IpSumResProdGetCarry : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t decay_check;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t sum_res_prod_get_carry_decay_0;
		bf_rt_id_t sum_res_prod_get_carry_decay_1;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpSumResProdGetCarry(const bfrt::BfRtInfo *info,
					  std::shared_ptr<bfrt::BfRtSession> session,
					  const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.stats_ip_a.sum_res_prod_get_carry") {
		init_key({
			{"ig_md.stats_ip.decay_check", &key_fields.decay_check},
		});

		init_actions({
			{"SwitchIngress_a.stats_ip_a.sum_res_prod_get_carry_decay_0",
			 &actions.sum_res_prod_get_carry_decay_0},
			{"SwitchIngress_a.stats_ip_a.sum_res_prod_get_carry_decay_1",
			 &actions.sum_res_prod_get_carry_decay_1},
		});

		// fill mac ip src decay check table
		add_entry(0, actions.sum_res_prod_get_carry_decay_0);
		add_entry(1, actions.sum_res_prod_get_carry_decay_1);
	}

private:
	void add_entry(uint32_t flag, bf_rt_id_t action_id) {
		key_setup(flag);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t flag) {
		table->keyReset(key.get());
		auto bf_status = key->setValue(key_fields.decay_check,
									   static_cast<uint64_t>(flag));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine